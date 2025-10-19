FROM python:3.10-slim

# Install Tesseract and image codecs for Pillow (JPEG/PNG/TIFF/WebP/JPEG2000)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    libtesseract-dev \
    libleptonica-dev \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    libopenjp2-7 \
    libtiff5 \
    libwebp6 \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY ./app /app/app

ENV PYTHONUNBUFFERED=1
# run with Gunicorn + Uvicorn workers for production
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-b", "0.0.0.0:8000", "--workers", "2", "--worker-connections", "1000"]
