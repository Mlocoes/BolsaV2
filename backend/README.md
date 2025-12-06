# Documentación del Backend - BolsaV2

## 📋 Descripción General

El backend de BolsaV2 está construido con **FastAPI**, un framework moderno y de alto rendimiento para construir APIs con Python 3.11+. Utiliza una arquitectura asíncrona para manejar múltiples solicitudes concurrentes de manera eficiente.

**Mejoras Recientes (v2.1):**
- **Alto Rendimiento:** Procesamiento paralelo de cotizaciones (`asyncio.gather`) y Caching distribuido con **Redis**.
- **Resiliencia:** Estrategia de fallback de 3 niveles (Cache -> DB -> Promedio) para garantizar disponibilidad de datos incluso si fallan las APIs externas.
- **Seguridad:** Cookies seguras, rate limiting y protección contra ataques comunes.

## 🛠️ Tecnologías Clave

- **FastAPI**: Framework web principal.
- **SQLAlchemy (Async)**: ORM para interactuar con la base de datos PostgreSQL de forma asíncrona.
- **Alembic**: Herramienta para migraciones de base de datos.
- **Pydantic**: Validación de datos y gestión de configuraciones.
- **Celery + Redis**: Cola de tareas para procesos en segundo plano (importación de datos, cálculos complejos).
- **Finnhub & Alpha Vantage**: Integraciones para obtener datos de mercado.

## 📂 Estructura del Proyecto

```
backend/
├── app/
│   ├── api/            # Endpoints de la API (v1)
│   ├── core/           # Configuración central, seguridad y middleware
│   ├── db/             # Modelos SQLAlchemy y configuración de sesión
│   ├── models/         # Definición de modelos de datos (Tablas)
│   ├── schemas/        # Esquemas Pydantic (Request/Response)
│   ├── services/       # Lógica de negocio (Finanzas, Importación, etc.)
│   └── main.py         # Punto de entrada de la aplicación
├── alembic/            # Versiones de migraciones de base de datos
├── tests/              # Pruebas unitarias e integración (Pytest)
└── requirements.txt    # Dependencias del proyecto
```

## 🚀 Configuración y Ejecución Local

### 1. Prerrequisitos
- Python 3.11 o superior
- PostgreSQL en ejecución
- Redis en ejecución

### 2. Instalación de Dependencias

Se recomienda usar un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Variables de Entorno

Crea un archivo `.env` en la carpeta `backend/` basado en el ejemplo (o usa el del root). Variables críticas:

- `DATABASE_URL`: `postgresql+asyncpg://user:pass@localhost/dbname`
- `SECRET_KEY`: Clave para firmar JWTs.
- `FINNHUB_API_KEY`: API Key para datos de mercado.
- `REDIS_URL`: `redis://localhost:6379/0` (Esencial para sesiones y caching).
- `FINNHUB_RATE_LIMIT`: `60` (Peticiones/minuto).

### 4. Ejecución del Servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en `http://localhost:8000`.
La documentación interactiva (Swagger UI) en `http://localhost:8000/docs`.

## 🧪 Pruebas

Ejecutar la suite de pruebas con Pytest:

```bash
pytest
```

## 🔄 Tareas en Segundo Plano (Celery)

Para iniciar el worker de Celery (necesario para importaciones):

```bash
celery -A app.services.celery_app worker --loglevel=info
```

## 🔐 Seguridad

- **Autenticación**: OAuth2 con Password Flow. Los tokens JWT tienen un tiempo de vida corto.
- **Sesiones**: Se utiliza un `SessionManager` basado en Redis/Memoria para invalidar sesiones activas instantáneamente (Logout real).
- **Hashing**: Las contraseñas se hashean usando `Argon2` o `Bcrypt` (vía Passlib).

## 📦 Modelos de Datos Principales

- **User**: Usuarios del sistema.
- **Asset**: Activos financieros (Acciones, ETFs, Cripto).
- **Quote**: Precios históricos (OHLCV).
- **Portfolio**: Carteras de inversión de usuarios.
- **Transaction**: Operaciones de compra/venta.
- **Snapshot**: Instantáneas históricas del valor del portafolio.
