# Product Requirements Document (PRD)

## Formación Evaluation Splitter — Excel-Email Automation

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Author** | Product Team |
| **Date Created** | 2026-03-04 |
| **Last Updated** | 2026-03-04 |
| **Status** | Implemented |
| **Stakeholders** | Departamento de Calidad, Tutores de Auditoría |
| **Target Users** | Equipo de Gestión de Formación / Calidad |
| **Priority** | P1 (High) |

---

## 1. Executive Summary

Esta aplicación automatiza la distribución de evaluaciones de formación (Formación) a cada Tutor responsable mediante correo electrónico. A partir de un archivo Excel de resumen de calificaciones, la app divide el archivo por Tutor, genera archivos individuales preservando todo el formato original (colores, fuentes, anchos de columna, estilos de relleno) y envía cada archivo como adjunto en un correo personalizado con soporte de contenido enriquecido (imágenes, formato avanzado).

---

## 2. Problem Statement

### 2.1 Current State

- El archivo Excel de evaluaciones de formación contiene las calificaciones de todos los profesionales agrupadas por Tutor.
- Actualmente, el responsable debe filtrar manualmente los datos por cada Tutor, copiar las filas correspondientes a un nuevo archivo, preservar manualmente los encabezados y formatos, y enviar cada archivo por correo individual.
- Este proceso es propenso a errores: se pueden omitir filas, perder formato, enviar datos incorrectos al Tutor equivocado, u olvidar columnas relevantes.
- El proceso manual puede tomar varias horas dependiendo del número de Tutores y profesionales.

### 2.2 Desired State

- El usuario importa el archivo Excel y la aplicación identifica automáticamente la estructura de encabezados multi-fila (filas 1-3) con categorías y subcategorías.
- La app detecta automáticamente la columna "Tutor" como criterio de división.
- Se muestra un ejemplo con los datos de un Tutor para que el usuario seleccione qué columnas incluir en los archivos divididos.
- Los archivos generados preservan fielmente todo el formato original: colores, fuentes, anchos/altos de celda, estilos de relleno y estructura de encabezados.
- El editor de correos permite insertar imágenes y utilizar funciones avanzadas de maquetación.
- Al enviar los correos, se preserva la maquetación y diseño del contenido.
- El tiempo de procesamiento se reduce de horas a minutos.

---

## 3. User Personas

### Primary User

| Attribute | Description |
|-----------|-------------|
| **Role** | Responsable de Gestión de Formación / Calidad |
| **Department** | Calidad / Auditoría |
| **Technical Level** | Medium |
| **Frequency of Use** | Quarterly / Semestral |
| **Number of Users** | 1-3 |

### Secondary User(s)

- **Tutores (receptores):** Reciben los archivos Excel individualizados con las evaluaciones de los profesionales a su cargo. No interactúan directamente con la aplicación.

---

## 4. Input Specification

### 4.1 Excel File Structure

| Attribute | Value |
|-----------|-------|
| **File Format** | .xlsx |
| **Typical File Size** | 100KB - 2MB |
| **Number of Rows** | 20-200 (variable según periodo y categoría) |
| **Number of Columns** | ~70 (C a BR) |
| **Has Header** | Yes |
| **Header Row(s)** | Rows 1-3 (multi-level header) |

### 4.2 Header Structure

El archivo utiliza un sistema de encabezados de 3 filas con celdas combinadas:

- **Row 1:** Valores de configuración/umbrales dispersos (mayormente vacía).
- **Row 2:** Categorías principales (celdas combinadas que agrupan subcategorías). Ejemplos: "Nota Formación", "CTP", "BLOQUE 1- ENTENDIMIENTO", "BLOQUE 2- CONTROLES Y RIESGOS", "NOTA FINAL CALIDAD", etc.
- **Row 3:** Subcategorías / nombres de columna individuales. Ejemplos: "Profesional", "DNI", "MAIL", "Tutor", cursos específicos, métricas de evaluación.

Algunas celdas de Row 2 están combinadas verticalmente con Row 3 (e.g., "Nota Formación", "Firma", "NOTA EVALUACIÓN"), indicando que son a la vez categoría y columna.

### 4.3 Column Definitions (Key Columns)

| Column | Letter | Name | Type | Description |
|--------|--------|------|------|-------------|
| 1 | C | (ID) | Number | Número identificador del profesional |
| 2 | D | Profesional | Text | Nombre completo del profesional (con acentos) |
| 3 | E | (Nombre sin acentos) | Text | Nombre sin caracteres especiales |
| 4 | F | DNI | Text | Documento Nacional de Identidad |
| 5 | G | MAIL | Text | Correo electrónico del profesional |
| 6 | H | (Email secundario) | Text | Email alternativo (no siempre presente) |
| 7 | I | **Tutor** | Text | **Columna de división** — Nombre del Tutor responsable |
| 8 | J-V | Cursos de Formación | Number/Text | Notas de cursos individuales (NA si no aplica) |
| 9 | W | (Total cursos) | Number | Suma de cursos completados |
| 10 | X | Nota Formación | Number | Nota global de formación |
| 11 | Y-Z | CTP | Number/Text | CTP 23/24 y Seguimiento Rojos/Naranjas |
| 12 | AA | Nota CTP | Number | Nota global CTP |
| 13 | AB-AI | INFLIGHT Bloques 1-4 | Number | Evaluaciones INFLIGHT por bloque (Entendimiento, Controles y Riesgos, D&I, Fraude) |
| 14 | AJ | Not Compliant ¿SOLVENTADO? | Text | Indicador de cumplimiento INFLIGHT |
| 15 | AK-AU | INFLIGHT Bloques 1-4 (detalle) | Number | Evaluaciones TOE AMRA/KAM, Especialistas, Circularización, Muestreo |
| 16 | AV | Not Compliant ¿SOLVENTADO? | Text | Indicador de cumplimiento (segundo bloque) |
| 17 | AW | Nota INFLIGHT | Number | Nota INFLIGHT calculada |
| 18 | AX | Nota INFLIGHT AJUSTADA | Number | Nota INFLIGHT ajustada |
| 19 | AY | Firma | Number | Indicador de firma |
| 20 | AZ | NOTA EVALUACIÓN | Number | Nota final de evaluación |
| 21 | BC-BG | Colaboración | Text/Number | Colaborador CTP, Formación, Grupo RCA, Falta/Retraso, Hojas de tiempo |
| 22 | BI | NOTA FINAL CALIDAD | Number | Nota final de calidad |
| 23 | BJ | ASPECTOS IDENTIFICADOS | Text | Observaciones y aspectos identificados (texto largo) |

### 4.4 Split Criteria

| Attribute | Value |
|-----------|-------|
| **Split By** | Tutor (nombre del tutor responsable) |
| **Split Column** | Column I — "Tutor" |
| **Block Identifier** | Cada fila con un valor en Column I pertenece al grupo de ese Tutor |
| **Subtotals** | No |
| **Grand Total** | No |

### 4.5 Sample Data

```
Row 1: [Config values / thresholds — mostly empty]
Row 2: [Categories]  | Nota Formación | CTP | BLOQUE 1- ENTENDIMIENTO | ... | NOTA FINAL CALIDAD | ASPECTOS IDENTIFICADOS
Row 3: [Subcategories] Profesional | DNI | MAIL | Tutor | Curso1 | Curso2 | ... | CTP 23/24 | ENTENDIMIENTO | WT | ...
Row 4: [Empty separator row]
Row 5: 17 | María Grande  | ... | Óscar Herranz | 2 | 2 | 2 | ...
Row 6: 34 | Marcos Ríos   | ... | Juan Berral   | 2 | 2 | 2 | ...
Row 7: 37 | Miguel Antelo  | ... | Juan Berral   | 2 | 2 | 2 | ...
Row 8: 40 | Angela Montilla| ... | María Gregorio| 2 | 2 | 2 | ...
...
```

**Tutores identificados en el archivo de ejemplo:**
- Ana Pidal
- Juan Berral
- María Gregorio
- Óscar Herranz

---

## 5. Split Modes

### Mode: By Tutor ("Por Tutor")

| Attribute | Value |
|-----------|-------|
| **Mode Identifier** | `tutor` |
| **Split Column** | I (Tutor) |
| **Block Identification Logic** | Agrupar todas las filas de datos (Row 5+) que comparten el mismo valor en la columna I "Tutor" |
| **Name Extraction** | Valor directo de la celda en columna I |
| **Data Rows** | Todas las filas desde Row 5 (o la primera fila con datos) hasta el final del archivo, excluyendo filas vacías |
| **Header Preservation** | Rows 1-3 se copian íntegramente a cada archivo generado, preservando celdas combinadas y formato |
| **Column Selection** | El usuario selecciona qué columnas incluir; la app muestra un ejemplo con datos de un Tutor para guiar la selección |

---

## 6. Output Specification

### 6.1 Generated Excel Files

| Attribute | Value |
|-----------|-------|
| **File Naming Convention** | `{Tutor_Name}_{Original_Filename}.xlsx` |
| **Template File** | None — se genera a partir del archivo original |
| **Include Header** | Yes — Rows 1-3 completas con celdas combinadas |
| **Include Subtotal** | No |
| **Column Selection** | User-selectable (guided by sample data preview) |
| **Default Columns** | All columns (user deselects unwanted ones) |
| **Formatting** | **Preserve original** — Colores, fuentes, anchos de columna, alturas de fila, estilos de relleno, bordes, celdas combinadas y toda propiedad visual del archivo original deben conservarse fielmente |

### 6.2 Email Specification

| Attribute | Value |
|-----------|-------|
| **Default Subject** | `Evaluación Formación — {{tutor_name}}` |
| **Default Body** | Ver plantilla abajo |
| **CC Recipients** | Configurable por el usuario |
| **Attachment** | Archivo Excel individual por Tutor |
| **Format** | HTML (con soporte de imágenes embebidas y formato avanzado) |

**Default Email Body Template:**
```html
<p>Estimado/a {{tutor_name}},</p>
<p>Adjunto encontrará el resumen de calificaciones de los profesionales a su cargo correspondiente al periodo de evaluación actual.</p>
<p>Por favor, revise la información y no dude en contactarnos si tiene alguna consulta.</p>
<p>Saludos cordiales,</p>
<p>Departamento de Calidad</p>
```

**Available Template Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `{{tutor_name}}` | Nombre completo del Tutor | "Juan Berral" |
| `{{num_profesionales}}` | Cantidad de profesionales asignados | "5" |
| `{{fecha}}` | Fecha de envío (DD/MM/YYYY) | "04/03/2026" |
| `{{periodo}}` | Periodo de evaluación | "2025" |

### 6.3 Rich Email Editor

| Feature | Description |
|---------|-------------|
| **Insertar imágenes** | Permitir al usuario insertar imágenes inline (logos, gráficos, firmas visuales) |
| **Formato de texto** | Negrita, cursiva, subrayado, color de texto, tamaño de fuente |
| **Listas** | Listas con viñetas y numeradas |
| **Tablas** | Insertar tablas HTML en el cuerpo del email |
| **Alineación** | Izquierda, centro, derecha, justificado |
| **Preservación al enviar** | Todo el formato y las imágenes embebidas deben mantenerse intactos al enviar vía Power Automate |

---

## 7. Contact Management

### 7.1 Contact Source

| Attribute | Value |
|-----------|-------|
| **Default Contacts File** | `data/Contactos_Tutores.xlsx` |
| **Contact Upload** | Required (primera vez) / Optional (si ya hay contactos guardados) |
| **Persistent Storage** | Yes |
| **Contact Fields** | Ver tabla abajo |

### 7.2 Contact File Columns

| Column | Letter | Field | Required |
|--------|--------|-------|----------|
| 1 | A | Tutor Name | Yes |
| 2 | B | Email | Yes |
| 3 | C | CC Email | No |

### 7.3 Contact Matching Logic

- Primary match by: Nombre del Tutor (coincidencia exacta con el valor de la columna I del archivo de evaluaciones)
- Fallback match by: Coincidencia parcial / fuzzy match por nombre
- Unmatched behavior: Marcado como no mapeado; el usuario puede proporcionar el email manualmente o excluir al Tutor del envío

---

## 8. SharePoint Integration (Optional)

Not applicable.

---

## 9. Functional Requirements

### 9.1 Core Requirements (Standard — inherited from standard spec)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Upload .xlsx file via web interface | P0 |
| FR-02 | Parse file and split by configured criteria | P0 |
| FR-03 | Display parsed groups with totals | P0 |
| FR-04 | Allow column selection for output | P1 |
| FR-05 | Load and map contacts | P0 |
| FR-06 | Configure email subject and body | P0 |
| FR-07 | Preview email before sending | P1 |
| FR-08 | Send emails via Power Automate | P0 |
| FR-09 | Display send results (success/failed) | P0 |
| FR-10 | Download generated files as ZIP | P1 |
| FR-11 | Persist contacts across sessions | P1 |
| FR-12 | Check Power Automate connectivity | P1 |

### 9.2 App-Specific Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-A01 | Intelligent multi-row header recognition (Rows 1-3) | P0 | Must detect merged cells, categories (Row 2) and subcategories (Row 3) automatically |
| FR-A02 | Auto-detect Tutor column as split key | P0 | Identify the "Tutor" column by label in Row 3 |
| FR-A03 | Sample-based column selection UI | P0 | Show data of one Tutor as example to guide the user in selecting which columns to include in the split files |
| FR-A04 | Full format preservation in split files | P0 | Preserve colors, fonts, column widths, row heights, fill patterns, borders, merged cells, and all visual formatting from the original file |
| FR-A05 | Preserve merged header cells in split output | P0 | The 3-row header with merged cells must be faithfully reproduced in each split file |
| FR-A06 | Rich text email editor with image support | P1 | WYSIWYG editor supporting images, text formatting, tables, and advanced layout |
| FR-A07 | Preserve email formatting on send | P1 | Ensure HTML content including embedded images is transmitted correctly via Power Automate |
| FR-A08 | Handle NA and formula values in data | P1 | Cells with "NA" text or formula results must be handled correctly during split |
| FR-A09 | Support variable header structures | P1 | Different evaluation files may have different column configurations; the app should not hardcode column positions |
| FR-A10 | Skip empty separator rows | P1 | Detect and skip empty rows (e.g., Row 4) between headers and data |

---

## 10. Non-Functional Requirements

| ID | Requirement | Specification |
|----|-------------|---------------|
| NFR-01 | File size limit | Max 50MB upload |
| NFR-02 | Processing time | < 30s for parse, < 60s per email send |
| NFR-03 | Availability | Office hours (8:00-20:00 local time) |
| NFR-04 | Browser support | Chrome 90+, Edge 90+, Firefox 90+ |
| NFR-05 | Concurrent users | 1 (single-user design) |
| NFR-06 | Data retention | Session data cleared on new upload |
| NFR-07 | Contact retention | Persistent until manual deletion |
| NFR-08 | Deployment | Docker or systemd on Linux |

---

## 11. User Interface

### 11.1 Workflow Steps

| Step | Name | User Action | System Response |
|------|------|-------------|----------------|
| 1 | Upload | Drag-and-drop or click to upload Excel file | Parse file, detect header structure (Rows 1-3), identify Tutor column, display summary |
| 2 | Column Selection | View sample data from one Tutor, check/uncheck columns to include | Display categories and subcategories with checkboxes; show preview of selected columns |
| 3 | Review Groups | View list of Tutors with count of professionals per Tutor | Display all Tutor groups with row counts |
| 4 | Contacts | Upload contacts file or use stored contacts | Map Tutors to email addresses, highlight unmapped Tutors |
| 5 | Email Compose | Edit subject and body using rich text editor; insert images | Show WYSIWYG editor with template variables; preview rendered email |
| 6 | Preview & Send | Review final email preview, click send | Send emails with formatted content and Excel attachments; display results |

### 11.2 UI Mockup / Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│  Formación Evaluation Splitter                                │
├──────────────────────────────────────────────────────────────┤
│  [1.Upload] → [2.Columns] → [3.Review] → [4.Contacts]       │
│            → [5.Email] → [6.Send]                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Step 2 — Column Selection (Sample: Juan Berral)             │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Category          │ Subcategory        │ ☑ Include  │     │
│  ├───────────────────┼────────────────────┼────────────┤     │
│  │ (General)         │ Profesional        │ ☑          │     │
│  │ (General)         │ DNI                │ ☐          │     │
│  │ (General)         │ MAIL               │ ☐          │     │
│  │ (General)         │ Tutor              │ ☑          │     │
│  │ Nota Formación    │ —                  │ ☑          │     │
│  │ CTP               │ CTP 23/24          │ ☑          │     │
│  │ BLOQUE 1          │ ENTENDIMIENTO      │ ☑          │     │
│  │ ...               │ ...                │ ...        │     │
│  │ NOTA FINAL CALIDAD│ —                  │ ☑          │     │
│  │ ASPECTOS IDENT.   │ —                  │ ☑          │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  Preview: [Showing 3 rows for Tutor "Juan Berral"]           │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│  Status: ● Power Automate Connected                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 12. Power Automate Configuration

| Attribute | Value |
|-----------|-------|
| **Email Flow Name** | FormacionApp - Send Email (TBD — configurar en Power Automate) |
| **Email Flow Owner** | Service account (TBD) |
| **SharePoint Flow Name** | N/A |
| **Sending Account** | TBD — configurar en Power Automate |
| **Environment** | Default |

---

## 13. Deployment

| Attribute | Value |
|-----------|-------|
| **Target Server** | TBD |
| **Deployment Method** | Docker (Dockerfile + docker-compose.yml incluidos) |
| **Port** | 8002 |
| **Domain/URL** | TBD |
| **SSL Required** | Recomendado (via reverse proxy) |

---

## 14. Testing Plan

### 14.1 Test Scenarios

| ID | Scenario | Expected Result | Priority |
|----|----------|----------------|----------|
| TC-01 | Upload valid Excel with multi-row headers | File parsed, 3-row header detected, Tutor column identified | P0 |
| TC-02 | Upload invalid file type (.csv, .xls) | Error message displayed | P0 |
| TC-03 | Parse file with 1 Tutor | Single group shown with all their professionals | P0 |
| TC-04 | Parse file with 4+ Tutors | All groups shown correctly | P0 |
| TC-05 | Column selection with sample preview | Sample data displayed correctly with category/subcategory hierarchy | P0 |
| TC-06 | Verify format preservation in split file | Colors, fonts, widths, heights, fill styles, merged cells preserved | P0 |
| TC-07 | Verify header rows (1-3) copied to split file | All 3 header rows with merged cells present in output | P0 |
| TC-08 | Map contacts — all Tutors matched | 0 unmapped Tutors | P0 |
| TC-09 | Map contacts — some Tutors unmapped | Unmapped Tutors highlighted for manual input | P0 |
| TC-10 | Compose email with images and rich formatting | Email preview shows formatted content with images | P1 |
| TC-11 | Send test email with rich content | Email received with formatting and images preserved | P0 |
| TC-12 | Send batch (4 Tutors) | All emails sent with correct individual attachments | P0 |
| TC-13 | Handle cells with "NA" values | NA values preserved correctly in split files | P1 |
| TC-14 | Handle cells with formula results | Formula results (not formulas) transferred correctly | P1 |
| TC-15 | Power Automate URL invalid | Error displayed on status check | P1 |
| TC-16 | Large file upload (50MB) | Processed within limits | P2 |
| TC-17 | Empty separator rows (Row 4) skipped | No empty rows in data output | P1 |

### 14.2 Acceptance Criteria

- [ ] All P0 test scenarios pass
- [ ] Multi-row header with merged cells correctly detected and preserved
- [ ] Email delivery confirmed to at least 3 different Tutors
- [ ] Split files are visually identical to original (format, colors, fonts, widths)
- [ ] Rich email content (images, formatting) preserved after sending
- [ ] Column selection UI correctly shows category/subcategory hierarchy
- [ ] Contact persistence works across app restarts
- [ ] Power Automate status check returns correctly
- [ ] Error messages are clear and actionable

---

## 15. Timeline & Milestones

| Milestone | Description | Target Date | Status |
|-----------|-------------|-------------|--------|
| M1 | PRD approved | 2026-03-04 | Completed |
| M2 | Backend development complete | 2026-03-05 | Completed |
| M3 | Frontend development complete | 2026-03-05 | Completed |
| M4 | Power Automate flows configured | TBD | Pending |
| M5 | Testing complete (unit tests) | 2026-03-05 | Completed (33 tests pass) |
| M6 | Deployment to production | TBD | Pending |
| M7 | User training | TBD | Pending |

---

## 16. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| Power Automate URL expires | Emails stop sending | Medium | Monitor, document regeneration process |
| Excel format changes between periods | Parse fails or column mapping breaks | Medium | Use intelligent label detection rather than hardcoded positions; validate headers |
| Service account password expires | Flows stop | Medium | Calendar reminder, service account |
| Complex merged cell structures not fully preserved | Split files lose visual fidelity | Medium | Use openpyxl with full style copy; test with multiple file variations |
| Rich email content stripped by email client | Recipients see broken formatting | Low | Test with major email clients (Outlook, Gmail); use inline CSS |
| Embedded images too large for Power Automate | Email send fails | Low | Compress images; enforce size limits in editor |
| Tutor name variations across periods | Contact matching fails | Medium | Implement fuzzy matching; allow manual override |

---

## 17. Appendix

### A. Glossary

| Term | Definition |
|------|-----------|
| Tutor | Responsable senior que supervisa a un grupo de profesionales en auditoría |
| Profesional | Empleado evaluado en el proceso de formación |
| Formación | Programa de formación / capacitación profesional |
| CTP | Continuous Training Program — Programa de formación continua |
| INFLIGHT | Revisión de calidad en curso (durante la ejecución de auditorías) |
| Not Compliant | Indicador de no cumplimiento en una evaluación INFLIGHT |
| BLOQUE | Bloque temático de evaluación INFLIGHT (Entendimiento, Controles, D&I, Fraude, etc.) |
| Nota Evaluación | Calificación global que combina Formación, CTP e INFLIGHT |
| NOTA FINAL CALIDAD | Nota final considerando todos los factores incluyendo colaboración |

### B. Related Documents

| Document | Location |
|----------|----------|
| Technical Specification | `docs/TECH_SPEC.md` |
| Architecture Design | `docs/ARCHITECTURE.md` |
| Conventions | `docs/CONVENTIONS.md` |
| Sample Excel File | `Ejemplo/2025-Notas evaluaciones Auditoria_Gerente y Socios.xlsx` |

### C. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-04 | Product Team | Initial version |
| 1.1 | 2026-03-05 | Development Team | Updated with implementation details, resolved TODOs |
