# BolsaV2 - Proyecto Completo

## ✅ Qué Incluye

### Backend (Python/FastAPI)
- Aplicación FastAPI con soporte asíncrono
- Modelos SQLAlchemy (Usuarios, Activos, Cotizaciones, Carteras, Operaciones, Resultados)
- Migraciones Alembic
- Autenticación con sesiones
- Hash de contraseñas con Argon2
- Contenedorización Docker

### Frontend (React/TypeScript)
- React 18 con TypeScript
- Herramienta de construcción Vite
- Tailwind CSS
- Gestión de estado con Zustand
- Páginas de Login y Panel de Control
- Docker + Nginx

### DevOps
- Orquestación con Docker Compose
- CI/CD con GitHub Actions
- Script de instalación
- Comandos Makefile

## 🚀 Inicio Rápido

```bash
chmod +x install.sh
./install.sh
```

Luego acceder a:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Documentación API: http://localhost:8000/docs

## 📝 Credenciales por Defecto

Usuario: admin (o el que hayas introducido)
Contraseña: admin123 (o la que hayas introducido)

## 🔧 Comandos

```bash
make build   # Construir imágenes
make up      # Iniciar servicios
make down    # Detener servicios
make logs    # Ver registros
```

## 📦 Qué Añadir

Esta es una versión mínima funcional. Para características completas, puedes añadir:
- Más endpoints de API (carteras, operaciones, cotizaciones)
- Páginas adicionales en el frontend
- Integración de Handsontable
- Recharts para análisis
- Funcionalidad de importación/exportación
- Pruebas más completas

## 🔐 Notas de Seguridad

- Cambiar SECRET_KEY en producción
- Usar contraseñas fuertes
- Habilitar HTTPS en producción
- Actualizar clave API de Finnhub

## 📄 Licencia

Licencia MIT
