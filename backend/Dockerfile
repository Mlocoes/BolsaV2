# Multi-stage build para optimizar el tamaño de la imagen
FROM python:3.11-alpine AS builder

ENV PYTHONUNBUFFERED=1

# Instalar dependencias de compilación necesarias
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

WORKDIR /app
COPY requirements.txt .

# Instalar dependencias en un directorio temporal
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Imagen final optimizada
FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1

# Solo instalar las dependencias de runtime
RUN apk add --no-cache \
    libpq \
    curl \
    libffi

WORKDIR /app

# Copiar las dependencias instaladas desde el builder
COPY --from=builder /install /usr/local

COPY . .

# Crear usuario no root para ejecutar la app de forma segura
RUN adduser -D -h /app appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
