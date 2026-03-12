"""Data persistence and history management service.

Manages:
- External data root at /home/rootadmin/data/Control_formacion
- temp/ folder for per-run temporary files (Excel, screenshots)
- basedata/ folder for templates, contacts, presets, runtime data
- History tracking (max N operations, auto-cleanup)
- Data sync between app local data/ and external data root
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import settings

logger = logging.getLogger(__name__)

# Files that should be synced between app/data and external basedata
SYNCABLE_FILES = [
    "contacts_store.json",
    "column_presets.json",
    "email_templates.json",
]


class DataManager:
    """Manages persistent data storage, temp files, and operation history."""

    def __init__(self):
        self._data_root = settings.data_root
        self._temp_path = settings.temp_path
        self._basedata_path = settings.basedata_path
        self._history_file = settings.history_file
        self._max_history = settings.max_history
        self._app_data = Path("data")

    # ── Directory Setup ──────────────────────────────────────────────

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        for d in (self._data_root, self._temp_path, self._basedata_path):
            d.mkdir(parents=True, exist_ok=True)
        self._app_data.mkdir(parents=True, exist_ok=True)
        logger.info("Data directories ensured: %s", self._data_root)

    # ── Data Sync ────────────────────────────────────────────────────

    def sync_data_on_startup(self) -> None:
        """Sync data between external basedata and app local data/.

        Strategy:
        - For each syncable file, use the newer version (by mtime).
        - If only one side has the file, copy it to the other side.
        """
        self.ensure_directories()

        for filename in SYNCABLE_FILES:
            app_file = self._app_data / filename
            ext_file = self._basedata_path / filename

            app_exists = app_file.exists()
            ext_exists = ext_file.exists()

            if app_exists and ext_exists:
                app_mtime = app_file.stat().st_mtime
                ext_mtime = ext_file.stat().st_mtime
                if ext_mtime > app_mtime:
                    shutil.copy2(str(ext_file), str(app_file))
                    logger.info("Synced %s: external → app (newer)", filename)
                elif app_mtime > ext_mtime:
                    shutil.copy2(str(app_file), str(ext_file))
                    logger.info("Synced %s: app → external (newer)", filename)
            elif app_exists and not ext_exists:
                shutil.copy2(str(app_file), str(ext_file))
                logger.info("Synced %s: app → external (new)", filename)
            elif ext_exists and not app_exists:
                shutil.copy2(str(ext_file), str(app_file))
                logger.info("Synced %s: external → app (new)", filename)

        logger.info("Data sync completed")

    def sync_data_to_external(self) -> None:
        """Push current app data files to external basedata."""
        self.ensure_directories()
        for filename in SYNCABLE_FILES:
            app_file = self._app_data / filename
            if app_file.exists():
                shutil.copy2(str(app_file), str(self._basedata_path / filename))

    # ── Temp / Run Management ────────────────────────────────────────

    def create_run_folder(self) -> Path:
        """Create a new timestamped run folder in temp/."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"run_{ts}"
        run_path = self._temp_path / run_id
        (run_path / "generated").mkdir(parents=True, exist_ok=True)
        (run_path / "screenshots").mkdir(parents=True, exist_ok=True)
        logger.info("Created run folder: %s", run_path)
        return run_path

    def save_run_files(
        self,
        run_path: Path,
        generated_files: List[Tuple[str, bytes]],
        screenshots: List[Tuple[str, bytes]],
    ) -> None:
        """Save generated files and screenshots into a run folder."""
        for fname, content in generated_files:
            (run_path / "generated" / fname).write_bytes(content)
        for fname, content in screenshots:
            (run_path / "screenshots" / fname).write_bytes(content)

    def load_run_files(
        self, run_path: Path
    ) -> Tuple[List[Tuple[str, bytes]], List[Tuple[str, bytes]]]:
        """Load generated files and screenshots from a run folder."""
        generated = []
        gen_dir = run_path / "generated"
        if gen_dir.exists():
            for f in sorted(gen_dir.iterdir()):
                if f.is_file():
                    generated.append((f.name, f.read_bytes()))

        screenshots = []
        scr_dir = run_path / "screenshots"
        if scr_dir.exists():
            for f in sorted(scr_dir.iterdir()):
                if f.is_file():
                    screenshots.append((f.name, f.read_bytes()))

        return generated, screenshots

    # ── History ──────────────────────────────────────────────────────

    def _load_history(self) -> List[Dict[str, Any]]:
        if self._history_file.exists():
            with open(self._history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("runs", [])
        return []

    def _save_history(self, runs: List[Dict[str, Any]]) -> None:
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._history_file, "w", encoding="utf-8") as f:
            json.dump({"runs": runs}, f, ensure_ascii=False, indent=2)

    def add_history_entry(
        self,
        run_path: Path,
        filename: str,
        tutors_count: int,
        files_count: int,
        emails_sent: int = 0,
        emails_failed: int = 0,
        status: str = "generated",
    ) -> Dict[str, Any]:
        """Add a new history entry and enforce max limit."""
        runs = self._load_history()

        entry = {
            "id": run_path.name,
            "path": str(run_path),
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "tutors_count": tutors_count,
            "files_count": files_count,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
            "status": status,
        }
        runs.insert(0, entry)

        # Enforce max history — delete old run folders
        while len(runs) > self._max_history:
            old = runs.pop()
            old_path = Path(old["path"])
            if old_path.exists():
                shutil.rmtree(str(old_path), ignore_errors=True)
                logger.info("Cleaned up old run: %s", old_path)

        self._save_history(runs)
        return entry

    def update_history_entry(self, run_id: str, **kwargs) -> None:
        """Update fields of an existing history entry."""
        runs = self._load_history()
        for run in runs:
            if run["id"] == run_id:
                run.update(kwargs)
                break
        self._save_history(runs)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get all history entries."""
        return self._load_history()

    def get_history_entry(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific history entry."""
        runs = self._load_history()
        return next((r for r in runs if r["id"] == run_id), None)

    def delete_history_entry(self, run_id: str) -> bool:
        """Delete a specific history entry and its files."""
        runs = self._load_history()
        entry = next((r for r in runs if r["id"] == run_id), None)
        if not entry:
            return False

        # Remove files
        run_path = Path(entry["path"])
        if run_path.exists():
            shutil.rmtree(str(run_path), ignore_errors=True)

        runs = [r for r in runs if r["id"] != run_id]
        self._save_history(runs)
        return True

    def cleanup_temp(self) -> int:
        """Remove all temp run folders not tracked in history."""
        runs = self._load_history()
        tracked_ids = {r["id"] for r in runs}
        removed = 0

        if self._temp_path.exists():
            for d in self._temp_path.iterdir():
                if d.is_dir() and d.name not in tracked_ids:
                    shutil.rmtree(str(d), ignore_errors=True)
                    removed += 1

        return removed
