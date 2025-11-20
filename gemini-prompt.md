# Prompt para Recrear el Sistema BolsaV3

Actúa como un Desarrollador Full Stack experto y arquitecto de software. Tu objetivo es diseñar y construir un sistema de gestión de carteras de inversión llamado "BolsaV3".

## Descripción del Proyecto
BolsaV3 es una aplicación web moderna para gestionar portafolios de inversión, rastrear transacciones, monitorear precios de activos y analizar el rendimiento histórico.

## Stack Tecnológico

### Backend
- **Framework:** FastAPI (Python) para una API REST de alto rendimiento.
- **Base de Datos:** PostgreSQL (con SQLAlchemy como ORM) y Alembic para migraciones.
- **Cache/Session:** Redis para gestión de sesiones y caché.
- **Tareas en Segundo Plano:** Celery para tareas asíncronas (ej. actualización de precios).
- **Seguridad:** Autenticación JWT, Rate Limiting (SlowAPI), Headers de seguridad.
- **Otros:** GZip middleware, Logging estructurado.

### Frontend
- **Framework:** React (con Vite) y TypeScript.
- **Estilos:** Tailwind CSS para un diseño moderno y responsivo.
- **Estado:** Zustand para gestión de estado global.
- **Componentes UI:** Lucide React (iconos), Handsontable (tablas de datos avanzadas), Recharts (gráficos financieros).
- **HTTP Client:** Axios.
- **Routing:** React Router DOM.

### Infraestructura
- **Contenedores:** Docker y Docker Compose para orquestación de servicios (Backend, Frontend, DB, Redis, Worker).
- **Servidor Web:** Nginx como reverse proxy.

## Funcionalidades Clave

1.  **Autenticación y Usuarios:**
    - Registro e inicio de sesión seguro.
    - Gestión de perfiles de usuario.

2.  **Gestión de Carteras (Portfolios):**
    - Crear múltiples carteras por usuario.
    - Visualizar resumen de valor total y rendimiento.

3.  **Activos y Transacciones:**
    - Base de datos de activos financieros.
    - Registro de transacciones (fecha, compra, venta, dividendos).
    - Cálculo automático de posiciones actuales.

4.  **Cotizaciones y Precios:**
    - Sistema para obtener y actualizar precios de activos (Scheduler).
    - Histórico de precios.

5.  **Análisis y Reportes:**
    - Snapshots diarios del valor de la cartera para seguimiento histórico.
    - Gráficos interactivos de rendimiento y composición.
    - Tablas de datos tipo Excel (Handsontable) para edición rápida.

6.  **Importación/Exportación:**
    - Capacidad de importar/exportar datos de transacciones.

## Requisitos de Diseño
- **Estética:** Diseño "Premium", moderno y limpio. Uso de modo oscuro/claro, paleta de colores profesional.
- **UX:** Interfaz reactiva, feedback inmediato al usuario (Toasts), transiciones suaves.

## Instrucciones de Implementación
1.  Configura la estructura del proyecto (monorepo o separado).
2.  Implementa los modelos de base de datos y la configuración de Docker.
3.  Desarrolla la API REST con los endpoints necesarios.
4.  Construye el frontend integrando los componentes visuales y la lógica de estado.
5.  Asegura la robustez con manejo de errores y validaciones.
