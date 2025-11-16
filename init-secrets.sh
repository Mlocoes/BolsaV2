#!/bin/bash

# Script para inicializar los archivos de secrets para Docker
# Este script debe ejecutarse antes de docker-compose up

set -e

SECRETS_DIR="./secrets"

echo "🔐 Inicializando Docker Secrets..."

# Crear directorio de secrets si no existe
if [ ! -d "$SECRETS_DIR" ]; then
    mkdir -p "$SECRETS_DIR"
    echo "✓ Directorio $SECRETS_DIR creado"
fi

# Función para crear secret desde .env o solicitar input
create_secret() {
    local secret_name=$1
    local env_var=$2
    local secret_file="$SECRETS_DIR/${secret_name}.txt"
    
    # Si el archivo ya existe, preguntar si sobrescribir
    if [ -f "$secret_file" ]; then
        read -p "⚠️  El archivo $secret_file ya existe. ¿Sobrescribir? (s/N): " overwrite
        if [[ ! "$overwrite" =~ ^[sS]$ ]]; then
            echo "  → Manteniendo archivo existente"
            return
        fi
    fi
    
    # Intentar obtener valor desde .env
    if [ -f ".env" ]; then
        value=$(grep "^${env_var}=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    fi
    
    # Si no se encuentra en .env, solicitar input
    if [ -z "$value" ]; then
        echo "❓ No se encontró $env_var en .env"
        read -sp "  Ingresa el valor para $secret_name: " value
        echo
    fi
    
    # Guardar en archivo
    echo -n "$value" > "$secret_file"
    chmod 600 "$secret_file"
    echo "✓ Secret creado: $secret_file"
}

# Crear secrets individuales
create_secret "db_password" "POSTGRES_PASSWORD"
create_secret "secret_key" "SECRET_KEY"
create_secret "finnhub_api_key" "FINNHUB_API_KEY"
create_secret "alpha_vantage_api_key" "ALPHA_VANTAGE_API_KEY"

echo ""
echo "✅ Inicialización de secrets completada"
echo ""
echo "📋 Archivos creados en $SECRETS_DIR:"
ls -lh "$SECRETS_DIR"
echo ""
echo "⚠️  IMPORTANTE: Estos archivos contienen información sensible."
echo "   Asegúrate de que estén en .gitignore y nunca los subas a git."
echo ""
echo "🚀 Ahora puedes ejecutar: docker-compose up -d"
