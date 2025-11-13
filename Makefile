.PHONY: help build up down logs test

help:
	@echo "Comandos BolsaV2:"
	@echo "  make build  - Construir imágenes"
	@echo "  make up     - Iniciar servicios"
	@echo "  make down   - Detener servicios"
	@echo "  make logs   - Ver registros"
	@echo "  make test   - Ejecutar pruebas"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	docker-compose exec backend pytest
