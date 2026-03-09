"""Excel generator service for creating individual files per Tutor."""

import logging
import re
import zipfile
from copy import copy
from io import BytesIO
from typing import List, Tuple, Optional, Dict

from openpyxl import load_workbook, Workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.utils import get_column_letter, column_index_from_string
from openpyxl.worksheet.worksheet import Worksheet

from models.schemas import ParsedDocument, DataBlock

logger = logging.getLogger(__name__)


class ExcelGenerator:
    """Generates individual Excel files per Tutor preserving original formatting."""

    def generate_files(
        self,
        document: ParsedDocument,
        source_content: bytes,
        selected_columns: List[str],
        original_filename: str = "",
    ) -> List[Tuple[str, bytes]]:
        """Generate individual Excel files for each Tutor.

        Args:
            document: Parsed document with blocks per Tutor
            source_content: Original uploaded file bytes
            selected_columns: Column letters to include in output
            original_filename: Original filename for naming convention

        Returns:
            List of (filename, content_bytes) tuples
        """
        source_wb = load_workbook(BytesIO(source_content), data_only=True)
        # Also load with styles (not data_only) for full formatting
        style_wb = load_workbook(BytesIO(source_content))
        source_ws = source_wb.active
        style_ws = style_wb.active

        files: List[Tuple[str, bytes]] = []

        # Build column mapping: source col letter -> output col index (1-based)
        col_mapping = self._build_column_mapping(selected_columns)

        # Collect merged cell ranges from source
        source_merges = list(style_ws.merged_cells.ranges)

        for block in document.blocks:
            if block.recipient.excluded:
                continue

            try:
                filename, content = self._generate_single_file(
                    source_ws, style_ws, block, col_mapping,
                    source_merges, original_filename,
                )
                files.append((filename, content))
            except Exception as e:
                logger.error("Error generando archivo para tutor %s: %s",
                             block.recipient.nombre, str(e))

        source_wb.close()
        style_wb.close()

        logger.info("Generados %d archivos individuales", len(files))
        return files

    def _generate_single_file(
        self,
        source_ws: Worksheet,
        style_ws: Worksheet,
        block: DataBlock,
        col_mapping: Dict[str, int],
        source_merges: list,
        original_filename: str,
    ) -> Tuple[str, bytes]:
        """Generate a single Excel file for one Tutor."""
        new_wb = Workbook()
        new_ws = new_wb.active
        new_ws.title = source_ws.title or "Evaluaciones"

        # Step 1: Copy header rows (1-3) with formatting
        for src_row in range(1, 4):
            dest_row = src_row
            self._copy_row_cells(style_ws, new_ws, src_row, dest_row, col_mapping)
            # Copy row height
            src_height = style_ws.row_dimensions[src_row].height
            if src_height:
                new_ws.row_dimensions[dest_row].height = src_height

        # Step 2: Copy merged cells in header rows (adjusted for column mapping)
        self._copy_header_merges(style_ws, new_ws, col_mapping, source_merges)

        # Step 3: Copy data rows for this Tutor
        dest_row = 4  # Start after headers (no separator row in output)
        for entry in block.entries:
            src_row = entry.source_row
            if src_row <= 0:
                continue
            self._copy_row_cells(style_ws, new_ws, src_row, dest_row, col_mapping)
            # Copy row height
            src_height = style_ws.row_dimensions[src_row].height
            if src_height:
                new_ws.row_dimensions[dest_row].height = src_height
            dest_row += 1

        # Step 4: Copy column widths for selected columns
        self._copy_column_widths(style_ws, new_ws, col_mapping)

        # Generate filename: {Tutor_Name}_{Original_Filename}.xlsx
        tutor_safe = self._sanitize_filename(block.recipient.nombre)
        base_name = original_filename.replace(".xlsx", "").replace(".xls", "")
        base_safe = self._sanitize_filename(base_name) if base_name else "Evaluacion"
        filename = f"{tutor_safe}_{base_safe}.xlsx"

        # Save to bytes
        buffer = BytesIO()
        new_wb.save(buffer)
        buffer.seek(0)
        content = buffer.read()
        new_wb.close()

        return filename, content

    def _copy_row_cells(
        self,
        source_ws: Worksheet,
        dest_ws: Worksheet,
        src_row: int,
        dest_row: int,
        col_mapping: Dict[str, int],
    ) -> None:
        """Copy cells from source row to dest row using column mapping."""
        for src_letter, dest_col_idx in col_mapping.items():
            src_col_idx = column_index_from_string(src_letter)
            source_cell = source_ws.cell(row=src_row, column=src_col_idx)
            dest_cell = dest_ws.cell(row=dest_row, column=dest_col_idx)

            # Skip MergedCell objects (they don't have actual values/styles)
            if isinstance(source_cell, MergedCell):
                continue

            # Copy value
            dest_cell.value = source_cell.value

            # Copy all formatting
            self._copy_cell_style(source_cell, dest_cell)

    def _copy_cell_style(self, source_cell, dest_cell) -> None:
        """Copy all formatting from source cell to destination cell."""
        if source_cell.font:
            dest_cell.font = copy(source_cell.font)
        if source_cell.fill and source_cell.fill.patternType:
            dest_cell.fill = copy(source_cell.fill)
        if source_cell.border:
            dest_cell.border = copy(source_cell.border)
        if source_cell.alignment:
            dest_cell.alignment = copy(source_cell.alignment)
        if source_cell.number_format:
            dest_cell.number_format = source_cell.number_format
        if source_cell.protection:
            dest_cell.protection = copy(source_cell.protection)

    def _copy_header_merges(
        self,
        source_ws: Worksheet,
        dest_ws: Worksheet,
        col_mapping: Dict[str, int],
        source_merges: list,
    ) -> None:
        """Copy merged cell ranges from headers, adjusting for column mapping."""
        selected_col_indices = set()
        for letter in col_mapping:
            selected_col_indices.add(column_index_from_string(letter))

        for merge_range in source_merges:
            min_row = merge_range.min_row
            max_row = merge_range.max_row

            # Only process header merges (rows 1-3)
            if min_row > 3:
                continue

            min_col = merge_range.min_col
            max_col = merge_range.max_col

            # Find which selected columns overlap with this merge range
            mapped_cols = []
            for src_col in range(min_col, max_col + 1):
                src_letter = get_column_letter(src_col)
                if src_letter in col_mapping:
                    mapped_cols.append(col_mapping[src_letter])

            if len(mapped_cols) < 2 and min_row == max_row:
                # Single cell in output — no merge needed for horizontal merges
                continue

            if mapped_cols:
                new_min_col = min(mapped_cols)
                new_max_col = max(mapped_cols)
                # Clamp max_row to 3 (headers only)
                new_max_row = min(max_row, 3)

                if new_min_col < new_max_col or min_row < new_max_row:
                    try:
                        dest_ws.merge_cells(
                            start_row=min_row,
                            start_column=new_min_col,
                            end_row=new_max_row,
                            end_column=new_max_col,
                        )
                    except ValueError:
                        pass  # Already merged or invalid range

    def _copy_column_widths(
        self,
        source_ws: Worksheet,
        dest_ws: Worksheet,
        col_mapping: Dict[str, int],
    ) -> None:
        """Copy column widths from source to destination."""
        for src_letter, dest_col_idx in col_mapping.items():
            src_width = source_ws.column_dimensions[src_letter].width
            dest_letter = get_column_letter(dest_col_idx)
            if src_width:
                dest_ws.column_dimensions[dest_letter].width = src_width
            else:
                dest_ws.column_dimensions[dest_letter].width = 12

    def _build_column_mapping(self, selected_columns: List[str]) -> Dict[str, int]:
        """Build mapping from source column letter to output column index.

        Selected columns are placed sequentially starting at column 1.
        """
        mapping: Dict[str, int] = {}
        # Sort columns by their original position to maintain order
        sorted_cols = sorted(selected_columns, key=lambda l: column_index_from_string(l))
        for idx, letter in enumerate(sorted_cols, start=1):
            mapping[letter] = idx
        return mapping

    def _sanitize_filename(self, name: str) -> str:
        """Create safe filename from a name string."""
        name = name.strip()
        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        name = name.replace(" ", "_")
        name = re.sub(r"_+", "_", name)
        if len(name) > 60:
            name = name[:60]
        return name.strip("_")

    def create_zip_archive(
        self, files: List[Tuple[str, bytes]], zip_filename: str = "evaluaciones.zip"
    ) -> bytes:
        """Create a ZIP archive containing all generated files."""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files:
                zf.writestr(filename, content)
        buffer.seek(0)
        return buffer.read()

    # ── Screenshot Generation ────────────────────────────────────────

    def generate_screenshots(
        self, files: List[Tuple[str, bytes]]
    ) -> List[Tuple[str, bytes]]:
        """Generate PNG screenshots for each generated Excel file.

        Args:
            files: List of (filename, content_bytes) from generate_files

        Returns:
            List of (png_filename, png_bytes) tuples
        """
        screenshots: List[Tuple[str, bytes]] = []
        for filename, content in files:
            try:
                png_name = filename.replace(".xlsx", ".png")
                png_content = self._render_excel_to_png(content)
                screenshots.append((png_name, png_content))
            except Exception as e:
                logger.error(
                    "Error generando captura para %s: %s", filename, str(e)
                )
        logger.info("Generadas %d capturas de pantalla", len(screenshots))
        return screenshots

    def _render_excel_to_png(self, file_content: bytes) -> bytes:
        """Render Excel file content as a PNG image using Pillow."""
        from PIL import Image, ImageDraw

        wb = load_workbook(BytesIO(file_content))
        ws = wb.active

        max_row = min(ws.max_row or 1, 100)
        max_col = min(ws.max_column or 1, 30)

        PADDING = 4
        MARGIN = 10
        DEFAULT_COL_WIDTH = 80
        DEFAULT_ROW_HEIGHT = 24
        FONT_SIZE = 11

        # Calculate column widths in pixels
        col_widths = []
        for col_idx in range(1, max_col + 1):
            letter = get_column_letter(col_idx)
            dim = ws.column_dimensions.get(letter)
            if dim and dim.width and dim.width > 0:
                px = max(int(dim.width * 7.5), 40)
                col_widths.append(min(px, 300))
            else:
                col_widths.append(DEFAULT_COL_WIDTH)

        # Calculate row heights in pixels
        row_heights = []
        for row_idx in range(1, max_row + 1):
            dim = ws.row_dimensions.get(row_idx)
            if dim and dim.height and dim.height > 0:
                px = max(int(dim.height * 1.33), 18)
                row_heights.append(px)
            else:
                row_heights.append(DEFAULT_ROW_HEIGHT)

        total_w = sum(col_widths) + MARGIN * 2
        total_h = sum(row_heights) + MARGIN * 2

        img = Image.new("RGB", (total_w, total_h), "#FFFFFF")
        draw = ImageDraw.Draw(img)

        font = self._get_pil_font(FONT_SIZE, bold=False)
        font_bold = self._get_pil_font(FONT_SIZE, bold=True)

        # Identify merged cells
        merged_map: Dict = {}
        for merge_range in ws.merged_cells.ranges:
            for r in range(merge_range.min_row, merge_range.max_row + 1):
                for c in range(merge_range.min_col, merge_range.max_col + 1):
                    if r <= max_row and c <= max_col:
                        if r == merge_range.min_row and c == merge_range.min_col:
                            rs = min(merge_range.max_row, max_row) - r + 1
                            cs = min(merge_range.max_col, max_col) - c + 1
                            merged_map[(r, c)] = (rs, cs)
                        else:
                            merged_map[(r, c)] = None

        # Draw cells
        y = MARGIN
        for row_idx in range(1, max_row + 1):
            x = MARGIN
            rh = row_heights[row_idx - 1]
            for col_idx in range(1, max_col + 1):
                w = col_widths[col_idx - 1]

                merge_info = merged_map.get((row_idx, col_idx), "normal")
                if merge_info is None:
                    x += w
                    continue

                cell_w = w
                cell_h = rh
                if isinstance(merge_info, tuple):
                    rs, cs = merge_info
                    cell_w = sum(col_widths[col_idx - 1 : col_idx - 1 + cs])
                    cell_h = sum(row_heights[row_idx - 1 : row_idx - 1 + rs])

                cell = ws.cell(row=row_idx, column=col_idx)

                # Background
                fill_color = "#FFFFFF"
                try:
                    if cell.fill and cell.fill.start_color:
                        rgb = cell.fill.start_color.rgb
                        if (
                            rgb
                            and isinstance(rgb, str)
                            and len(rgb) >= 6
                            and rgb != "00000000"
                        ):
                            fill_color = "#" + rgb[-6:]
                except Exception:
                    pass

                rect = [x, y, x + cell_w - 1, y + cell_h - 1]
                draw.rectangle(rect, fill=fill_color)
                draw.rectangle(rect, outline="#CCCCCC")

                # Text
                value = cell.value
                if value is not None:
                    text = str(value)
                    if len(text) > 50:
                        text = text[:47] + "..."

                    is_bold = bool(cell.font and cell.font.bold)
                    text_font = font_bold if is_bold else font

                    text_color = "#000000"
                    try:
                        if cell.font and cell.font.color and cell.font.color.rgb:
                            tc = cell.font.color.rgb
                            if (
                                isinstance(tc, str)
                                and len(tc) >= 6
                                and tc != "00000000"
                            ):
                                text_color = "#" + tc[-6:]
                    except Exception:
                        pass

                    text_x = x + PADDING
                    text_y = y + (rh - FONT_SIZE) // 2

                    try:
                        if cell.alignment:
                            if cell.alignment.horizontal == "center":
                                bbox = draw.textbbox((0, 0), text, font=text_font)
                                tw = bbox[2] - bbox[0]
                                text_x = x + (cell_w - tw) // 2
                            elif cell.alignment.horizontal == "right":
                                bbox = draw.textbbox((0, 0), text, font=text_font)
                                tw = bbox[2] - bbox[0]
                                text_x = x + cell_w - tw - PADDING
                    except Exception:
                        pass

                    draw.text(
                        (text_x, text_y), text, fill=text_color, font=text_font
                    )

                x += w
            y += rh

        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        wb.close()
        return buffer.read()

    @staticmethod
    def _get_pil_font(size: int = 11, bold: bool = False):
        """Get a PIL font, trying system fonts first."""
        from PIL import ImageFont

        if bold:
            names = ["arialbd.ttf", "calibrib.ttf", "DejaVuSans-Bold.ttf"]
        else:
            names = ["arial.ttf", "calibri.ttf", "DejaVuSans.ttf"]

        for name in names:
            try:
                return ImageFont.truetype(name, size)
            except (OSError, IOError):
                pass

        try:
            return ImageFont.load_default(size)
        except TypeError:
            return ImageFont.load_default()
