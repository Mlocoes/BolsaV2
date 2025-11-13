#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

echo -e "${BLUE}Instalación de BolsaV2${NC}"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado"
    exit 1
fi

# Crear .env si no existe
if [ ! -f ".env" ]; then
    print_info "Creando archivo .env..."
    
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "cambiar-esta-clave-secreta-$(date +%s)")
    
    read -p "Contraseña de base de datos [bolsav2pass]: " DB_PASSWORD
    DB_PASSWORD=${DB_PASSWORD:-bolsav2pass}
    
    read -p "Nombre de usuario administrador [admin]: " ADMIN_USERNAME
    ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
    
    read -p "Correo electrónico del administrador [admin@bolsav2.com]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@bolsav2.com}
    
    read -sp "Contraseña del administrador: " ADMIN_PASSWORD
    echo ""
    [ -z "$ADMIN_PASSWORD" ] && ADMIN_PASSWORD="admin123"
    
    read -p "Clave API de Finnhub (obtenerla en finnhub.io): " FINNHUB_API_KEY
    [ -z "$FINNHUB_API_KEY" ] && FINNHUB_API_KEY="demo-key"
    
    cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql+asyncpg://bolsav2_user:${DB_PASSWORD}@db:5432/bolsav2
POSTGRES_USER=bolsav2_user
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=bolsav2
REDIS_URL=redis://redis:6379/0
FINNHUB_API_KEY=${FINNHUB_API_KEY}
CORS_ORIGINS=http://localhost:3000
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
VITE_API_BASE_URL=http://localhost:8000/api/v1
EOF
    
    print_success "Archivo .env creado"
fi

# Construir e iniciar
print_info "Construyendo imágenes Docker..."
docker-compose build

print_info "Iniciando base de datos..."
docker-compose up -d db redis
sleep 10

print_info "Ejecutando migraciones..."
docker-compose run --rm backend alembic upgrade head

print_info "Creando usuario administrador..."
docker-compose run --rm backend python -m app.scripts.create_admin

print_info "Iniciando todos los servicios..."
docker-compose up -d

echo ""
print_success "¡Instalación completada!"
echo ""
print_info "Acceder a la aplicación:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  Docs API:  http://localhost:8000/docs"
echo ""
print_info "Credenciales por defecto:"
echo "  Usuario: ${ADMIN_USERNAME:-admin}"
echo "  Contraseña: (la que has introducido)"
