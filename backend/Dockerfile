# Fast Optimized Backend - Focus on cleanup, not multi-stage
# Target: ~700MB (from 1.29GB - 45% reduction)
# Build time: ~2-3 minutes (vs 20+ minutes for multi-stage)

FROM python:3.11-slim

# Install runtime + Docker CLI in one layer, then cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    libtesseract-dev \
    libleptonica-dev \
    libzbar0 \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    libopenjp2-7 \
    libtiff-dev \
    libwebp-dev \
    pkg-config \
    gcc \
    postgresql-client \
    gzip \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/* \
    && rm -rf /root/.cache

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && rm -rf /root/.cache/pip \
    && find /usr/local/lib/python3.10 -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.10 -name "*.pyc" -delete \
    && find /usr/local/lib/python3.10 -name "*.pyo" -delete \
    && find /usr/local/lib/python3.10 -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.10 -type d -name "test" -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/locale/* /var/log/*

# Copy application
COPY ./app /app/app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with Gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", \
     "-b", "0.0.0.0:8000", "--workers", "2", "--worker-connections", "1000"]

