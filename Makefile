.PHONY: help build up down logs test

help:
	@echo "BolsaV2 Commands:"
	@echo "  make build  - Build images"
	@echo "  make up     - Start services"
	@echo "  make down   - Stop services"
	@echo "  make logs   - View logs"
	@echo "  make test   - Run tests"

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
