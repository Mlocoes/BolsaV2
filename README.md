# BolsaV2 - Sistema de Gestión de Carteras de Inversión

BolsaV2 es una aplicación robusta, segura y escalable para la gestión de carteras de inversión, diseñada con una arquitectura moderna de microservicios.

[![CI](https://github.com/Mlocoes/BolsaV2/workflows/CI/badge.svg)](https://github.com/Mlocoes/BolsaV2/actions)

## 🚀 Características Principales

### Backend (Python/FastAPI)
- **API RESTful asíncrona** construida con FastAPI.
- **Base de datos PostgreSQL** con modelos SQLAlchemy y migraciones Alembic.
- **Autenticación segura** con sesiones efímeras en memoria (no persistentes en disco) y hash de contraseñas Argon2.
- **Integración con Finnhub** para cotizaciones de mercado en tiempo real e históricas.
- **Gestión de tareas en segundo plano** (Workers) para importaciones masivas y cálculos pesados.
- **Seguridad**: Rate limiting, validación de esquemas con Pydantic, protección CORS.

### Frontend (React/TypeScript)
- **Interfaz moderna y responsiva** construida con React 18, Vite y Tailwind CSS.
- **Tablas de datos avanzadas** utilizando Handsontable para una experiencia tipo hoja de cálculo.
- **Gestión de estado global** con Zustand.
- **Visualización de datos** con gráficos interactivos.
- **Diseño modular** orientado a componentes.

### DevOps & Infraestructura
- **Dockerización completa** de todos los servicios (Backend, Frontend, DB, Redis, Workers).
- **Orquestación** sencilla mediante Docker Compose.
- **Secret Management** utilizando Docker Secrets.
- **CI/CD** configurado con GitHub Actions.

## 🛠️ Tech Stack

- **Lenguajes:** Python 3.11+, TypeScript, SQL.
- **Frameworks:** FastAPI, React, Tailwind CSS.
- **Base de Datos:** PostgreSQL 15.
- **Cache/Cola:** Redis 7.
- **Herramientas:** Docker, Docker Compose, Make, Nginx.

## 📋 Prerrequisitos

- Docker y Docker Compose instalados.
- Make (opcional, para usar los comandos rápidos).
- Git.

## ⚡ Inicio Rápido

La forma más sencilla de iniciar el proyecto es utilizando el script de instalación interactivo:

```bash
chmod +x install.sh
./install.sh
```

Este script te guiará a través de:
1. Verificación de dependencias.
2. Configuración de variables de entorno (`.env`).
3. Creación de base de datos y usuario administrador.
4. Despliegue de contenedores.

### Accesos por defecto
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Documentación API (Swagger):** http://localhost:8000/docs
- **PgAdmin (si habilitado):** http://localhost:5050

## 👨‍💻 Flujo de Desarrollo

### Comandos Útiles (Makefile)

```bash
make help      # Muestra todos los comandos disponibles
make build     # Construye las imágenes de Docker
make up        # Levanta todos los servicios en segundo plano
make down      # Detiene y elimina los contenedores
make logs      # Muestra los logs de todos los servicios
make test      # Ejecuta los tests del backend
make migrate   # Ejecuta migraciones de base de datos pendientes
```

### ⚠️ Nota Importante sobre Frontend y Docker

El entorno de desarrollo actual utiliza Docker para servir el frontend. **No hay "Hot Reload" automático para cambios en el código del frontend cuando se ejecuta dentro de Docker**, ya que la aplicación se compila al construir la imagen.

**Si realizas cambios en el código del frontend (React/CSS/TSX), debes reconstruir el contenedor para verlos reflejados:**

```bash
# Reconstruir solo el frontend y reiniciar el servicio
docker-compose up -d --build frontend
```

O usando Make (si está configurado):
```bash
make rebuild-front
```

## 📂 Estructura del Proyecto

```
BolsaV2/
├── backend/                # Código fuente del Backend (FastAPI)
│   ├── app/
│   │   ├── api/            # Endpoints de la API
│   │   ├── core/           # Configuración y seguridad
│   │   ├── db/             # Modelos y conexión DB
│   │   ├── services/       # Lógica de negocio e integraciones
│   │   └── main.py         # Punto de entrada
│   ├── alembic/            # Migraciones de BD
│   └── Dockerfile
├── frontend/               # Código fuente del Frontend (React)
│   ├── src/
│   │   ├── components/     # Componentes reutilizables
│   │   ├── pages/          # Vistas principales
│   │   ├── services/       # Clientes de API
│   │   └── styles/         # Estilos globales y custom
│   └── Dockerfile
├── secrets/                # Archivos de secretos (no versionados)
├── docker-compose.yml      # Orquestación de servicios
├── install.sh              # Script de instalación
├── Makefile                # Atajos de comandos
└── README.md               # Documentación
```

## 🔒 Seguridad

- **Credenciales:** Nunca commitear archivos `.env` o contenidos de la carpeta `secrets/`.
- **Sesiones:** Las sesiones de usuario se almacenan en memoria y se invalidan al reiniciar el servicio de backend, garantizando que no persistan tokens obsoletos.
- **Producción:** Para despliegues en producción, asegúrese de cambiar `SECRET_KEY`, habilitar HTTPS y configurar un proxy inverso adecuado (Nginx/Traefik).

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
