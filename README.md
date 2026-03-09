# Formación Evaluation Splitter

Aplicación web para automatizar la distribución de evaluaciones de formación a cada Tutor responsable mediante correo electrónico.

A partir de un archivo Excel de resumen de calificaciones, la app divide el archivo por Tutor, genera archivos individuales preservando todo el formato original y envía cada archivo como adjunto en un correo personalizado con contenido enriquecido.

---

## Características

- **Parsing inteligente** — Detecta automáticamente encabezados multi-fila (Filas 1-3) con celdas combinadas y categorías/subcategorías
- **División por Tutor** — Identifica la columna "Tutor" y agrupa los datos automáticamente
- **Selección de columnas** — Permite elegir qué columnas incluir, con vista previa de datos de ejemplo
- **Preservación de formato** — Los archivos generados mantienen colores, fuentes, bordes, anchos de columna, alturas de fila y celdas combinadas del original
- **Capturas de alta fidelidad** — Generación de PNG desde Excel vía LibreOffice + PyMuPDF, preservando todos los estilos, colores y valores calculados de fórmulas
- **Matching de contactos** — Coincidencia exacta, sin acentos (NFKD) y por tokens parciales
- **Editor de email rico** — Negrita, cursiva, color, imágenes inline, tablas, listas
- **Envío vía Power Automate** — HTTP POST con adjuntos Base64, modo test incluido
- **Contactos persistentes** — Almacenamiento JSON reutilizable entre sesiones

---

## Requisitos

- Python ≥ 3.9
- **LibreOffice** (para generación de capturas de pantalla PNG desde archivos Excel)
  - Windows: Descargar desde [libreoffice.org](https://www.libreoffice.org/download/)
  - Linux: `apt-get install libreoffice-calc`
  - Docker: Se instala automáticamente (ver Dockerfile)
- Power Automate flow configurado para envío de emails (ver [Configuración de Power Automate](#configuración-de-power-automate))

---

## Instalación

### Opción 1: Ejecución directa

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd Control_formacion

# 2. Crear entorno virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores correspondientes (ver sección Configuración)

# 5. Ejecutar la aplicación
python main.py
```

La aplicación estará disponible en `http://localhost:8002`.

### Opción 2: Docker

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores correspondientes

# 2. Crear directorio de datos
mkdir -p data

# 3. Ejecutar con Docker Compose
docker-compose up -d
```

La aplicación estará disponible en `http://localhost:8002`.

Para ver los logs:
```bash
docker-compose logs -f
```

Para detener:
```bash
docker-compose down
```

---

## Configuración

### Variables de entorno (.env)

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `POWER_AUTOMATE_URL` | **Sí** | `""` | URL del webhook de Power Automate para envío de emails |
| `CONTACTS_FILE_PATH` | No | `data/Contactos_Tutores.xlsx` | Ruta al archivo de contactos por defecto |
| `CONTACTS_STORE_PATH` | No | `data/contacts_store.json` | Ruta al almacén persistente de contactos |
| `CONTACTS_DELETE_PASSWORD` | No | `Formacion2026` | Contraseña para eliminar contactos almacenados |
| `DEFAULT_CC_EMAILS` | No | `""` | Emails CC por defecto (separados por coma) |
| `HOST` | No | `0.0.0.0` | Host del servidor |
| `PORT` | No | `8002` | Puerto del servidor |
| `DEBUG` | No | `false` | Modo debug |

### Archivo de contactos

El archivo de contactos (`Contactos_Tutores.xlsx`) debe tener las siguientes columnas:

| Columna | Letra | Campo | Requerido |
|---------|-------|-------|-----------|
| 1 | A | Nombre del Tutor | Sí |
| 2 | B | Email | Sí |
| 3 | C | Email CC | No |

---

## Uso paso a paso

### Paso 1 — Subir archivo Excel

1. Abrir `http://localhost:8002` en el navegador
2. Arrastrar el archivo `.xlsx` de evaluaciones a la zona de carga, o hacer clic para seleccionarlo
3. La app detectará automáticamente la estructura de encabezados y la columna "Tutor"

### Paso 2 — Seleccionar columnas

1. Se muestra una vista previa con los datos de un Tutor de ejemplo
2. Las columnas están organizadas por categoría (de la Fila 2 del Excel)
3. Marcar/desmarcar las columnas que se desean incluir en los archivos individuales
4. Usar los botones de categoría para seleccionar/deseleccionar grupos completos

### Paso 3 — Revisar grupos

1. Se muestran todos los Tutores identificados con el número de profesionales asignados
2. Se generan los archivos Excel individuales
3. Opción de descargar archivos individuales o todos como ZIP

### Paso 4 — Mapear contactos

1. **Primera vez:** Subir el archivo `Contactos_Tutores.xlsx` con los emails de cada Tutor
2. **Siguientes veces:** Los contactos se cargan automáticamente del almacén persistente
3. Verificar la tabla de mapeo: cada Tutor debe tener un email asignado
4. Completar manualmente los emails de Tutores no mapeados

### Paso 5 — Componer email

1. Editar el asunto del correo (soporta la variable `{{tutor_name}}`)
2. Usar el editor de texto enriquecido para componer el cuerpo del email:
   - **Formato:** Negrita, cursiva, subrayado
   - **Fuente:** Tamaño y color de texto
   - **Estructura:** Listas con viñetas/numeradas, tablas
   - **Imágenes:** Insertar desde URL o archivo local
   - **Alineación:** Izquierda, centro, derecha, justificado
3. Variables disponibles (se sustituyen automáticamente por cada Tutor):
   - `{{tutor_name}}` — Nombre del Tutor
   - `{{num_profesionales}}` — Cantidad de profesionales
   - `{{fecha}}` — Fecha de envío (DD/MM/YYYY)
   - `{{periodo}}` — Periodo de evaluación

### Paso 6 — Previsualizar y enviar

1. Revisar la vista previa del email
2. Opcionalmente excluir Tutores específicos del envío
3. **Modo test:** Enviar un solo email de prueba antes del envío masivo
4. Hacer clic en "Enviar" para el envío por lotes
5. Ver los resultados por cada Tutor (éxito/fallo/excluido)

---

## Configuración de Power Automate

### Crear el flow de envío de email

1. Ir a [Power Automate](https://make.powerautomate.com)
2. Crear un nuevo flow **"Instant cloud flow"** con trigger **"When an HTTP request is received"**
3. Configurar el esquema JSON del body:

```json
{
    "type": "object",
    "properties": {
        "to": { "type": "string" },
        "cc": { "type": "string" },
        "subject": { "type": "string" },
        "body": { "type": "string" },
        "isHtml": { "type": "boolean" },
        "attachmentName": { "type": "string" },
        "attachmentContent": { "type": "string" }
    }
}
```

4. Añadir la acción **"Send an email (V2)"** de Office 365 Outlook:
   - **To:** `@{triggerBody()?['to']}`
   - **Subject:** `@{triggerBody()?['subject']}`
   - **Body:** `@{triggerBody()?['body']}`
   - **CC:** `@{triggerBody()?['cc']}`
   - **Is HTML:** `@{triggerBody()?['isHtml']}`
   - **Attachments Name:** `@{triggerBody()?['attachmentName']}`
   - **Attachments Content:** `@{base64ToBinary(triggerBody()?['attachmentContent'])}`

5. Guardar el flow y copiar la **HTTP POST URL**
6. Pegar la URL en el archivo `.env`:

```env
POWER_AUTOMATE_URL=https://prod-XX.westeurope.logic.azure.com/workflows/...
```

---

## Formato del archivo Excel de entrada

El archivo debe tener la siguiente estructura:

```
Fila 1: Valores de configuración / umbrales (mayormente vacía)
Fila 2: Categorías principales (celdas combinadas)
Fila 3: Subcategorías / nombres de columna individuales
Fila 4: (fila separadora vacía — se omite automáticamente)
Fila 5+: Datos de profesionales
```

**Requisito clave:** Debe existir una columna con el encabezado **"Tutor"** en la Fila 3. Esta columna se usa como criterio de división.

---

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/` | Frontend SPA |
| `POST` | `/api/parse` | Subir y parsear archivo Excel |
| `POST` | `/api/set-columns` | Seleccionar columnas para los archivos |
| `POST` | `/api/generate-files` | Generar archivos Excel individuales |
| `GET` | `/api/download-zip` | Descargar todos los archivos como ZIP |
| `GET` | `/api/download-file/{filename}` | Descargar un archivo específico |
| `POST` | `/api/map-contacts` | Mapear contactos de Tutores |
| `GET` | `/api/contacts/stored` | Ver contactos almacenados |
| `POST` | `/api/contacts/delete` | Eliminar contactos (requiere contraseña) |
| `GET` | `/api/template` | Obtener plantilla de email actual |
| `POST` | `/api/template` | Actualizar plantilla de email |
| `GET` | `/api/preview-email` | Previsualizar email |
| `GET` | `/api/power-automate/status` | Verificar conexión con Power Automate |
| `POST` | `/api/send` | Enviar emails |

---

## Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests de un módulo específico
pytest tests/test_parser.py -v
pytest tests/test_generator.py -v
pytest tests/test_mapper.py -v
pytest tests/test_sender.py -v
```

**Estado actual:** 33 tests — todos pasando.

---

## Estructura del proyecto

```
Control_formacion/
├── main.py                     # Aplicación FastAPI (punto de entrada)
├── config.py                   # Configuración (Pydantic BaseSettings)
├── requirements.txt            # Dependencias Python
├── .env.example                # Plantilla de variables de entorno
├── Dockerfile                  # Configuración Docker
├── docker-compose.yml          # Docker Compose
├── models/
│   ├── __init__.py
│   └── schemas.py              # Modelos de datos Pydantic
├── services/
│   ├── __init__.py
│   ├── excel_parser.py         # Parsing de encabezados multi-fila
│   ├── excel_generator.py      # Generación de archivos con formato
│   ├── contact_mapper.py       # Mapeo fuzzy de contactos
│   └── email_sender.py         # Envío via Power Automate
├── static/
│   ├── index.html              # Frontend SPA (wizard 6 pasos)
│   └── images/                 # Imágenes para plantillas de email
├── templates/
│   └── email_default.html      # Plantilla de email por defecto
├── data/                       # Datos en runtime
│   ├── .gitkeep
│   ├── contacts_store.json     # Contactos persistentes (auto-generado)
│   └── Contactos_Tutores.xlsx  # Archivo de contactos
├── tests/                      # Tests unitarios (33 tests)
├── docs/                       # Documentación del proyecto
│   ├── PRD.md
│   ├── TECH_SPEC.md
│   ├── ARCHITECTURE.md
│   └── CONVENTIONS.md
└── Ejemplo/                    # Archivos de ejemplo
    └── 2025-Notas evaluaciones Auditoria_Gerente y Socios.xlsx
```

---

## Notas técnicas

- **Puerto asignado:** 8002 (único por app, evita conflictos con otros servicios)
- **Worker único:** Uvicorn se ejecuta con `--workers 1` para mantener el estado de sesión en memoria
- **Diseño single-user:** La app está diseñada para un usuario a la vez
- **Sesión en memoria:** Los datos de sesión se pierden al reiniciar el servidor
- **Contactos persistentes:** Los contactos mapeados se guardan en JSON y se reutilizan entre sesiones
- **Eliminación de contactos:** Requiere la contraseña configurada en `CONTACTS_DELETE_PASSWORD`

---

## Tecnologías

| Componente | Tecnología |
|------------|-----------|
| Backend | Python 3.9+ / FastAPI |
| Excel | openpyxl |
| Capturas PNG | LibreOffice (headless) + PyMuPDF |
| Validación | Pydantic v2 |
| Email | Power Automate (HTTP POST) |
| Frontend | HTML5 + CSS + Vanilla JavaScript |
| Deploy | Docker / Uvicorn |
