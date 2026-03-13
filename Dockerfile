FROM python:3.11-slim

WORKDIR /app

# Install LibreOffice (headless) for Excel→PDF screenshot conversion
# fonts-* are required — without them LibreOffice renders blank pages on slim images
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libreoffice-calc \
        fonts-dejavu-core \
        fonts-liberation \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Writable LibreOffice user profile directory (avoids ~/.config write failures)
ENV HOME=/tmp

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p /app/data \
    && mkdir -p /home/rootadmin/data/Control_formacion/temp \
    && mkdir -p /home/rootadmin/data/Control_formacion/basedata

# Expose port
EXPOSE 8002

# Run with single worker (required for session state)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
