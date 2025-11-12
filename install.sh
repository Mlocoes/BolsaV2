#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

echo -e "${BLUE}BolsaV2 Installation${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not installed"
    exit 1
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change-this-secret-key-$(date +%s)")
    
    read -p "Database password [bolsav2pass]: " DB_PASSWORD
    DB_PASSWORD=${DB_PASSWORD:-bolsav2pass}
    
    read -p "Admin username [admin]: " ADMIN_USERNAME
    ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
    
    read -p "Admin email [admin@bolsav2.com]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@bolsav2.com}
    
    read -sp "Admin password: " ADMIN_PASSWORD
    echo ""
    [ -z "$ADMIN_PASSWORD" ] && ADMIN_PASSWORD="admin123"
    
    read -p "Finnhub API Key (get from finnhub.io): " FINNHUB_API_KEY
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
    
    print_success ".env created"
fi

# Build and start
print_info "Building Docker images..."
docker-compose build

print_info "Starting database..."
docker-compose up -d db redis
sleep 10

print_info "Running migrations..."
docker-compose run --rm backend alembic upgrade head

print_info "Creating admin user..."
docker-compose run --rm backend python -m app.scripts.create_admin

print_info "Starting all services..."
docker-compose up -d

echo ""
print_success "Installation complete!"
echo ""
print_info "Access the application:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
print_info "Default credentials:"
echo "  Username: ${ADMIN_USERNAME:-admin}"
echo "  Password: (the one you entered)"
