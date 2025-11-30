# Documentación de Base de Datos - BolsaV2

## 🗄️ Descripción General

BolsaV2 utiliza **PostgreSQL** como sistema de gestión de base de datos relacional. El esquema está diseñado para garantizar la integridad de las transacciones financieras y permitir consultas eficientes de datos históricos.

## 🏗️ Esquema de Base de Datos

### Tablas Principales

1.  **users**
    *   Almacena la información de autenticación y perfil de los usuarios.
    *   `id` (UUID), `email` (Unique), `hashed_password`, `is_active`.

2.  **assets**
    *   Catálogo maestro de instrumentos financieros.
    *   `id` (UUID), `symbol` (Unique, ej: AAPL), `name`, `asset_type` (stock, etf, crypto), `currency`.

3.  **portfolios**
    *   Contenedor lógico para las inversiones de un usuario.
    *   `id` (UUID), `user_id` (FK), `name`, `description`.

4.  **transactions**
    *   Registro inmutable de cada operación (compra, venta, dividendo).
    *   `id` (UUID), `portfolio_id` (FK), `asset_id` (FK), `type` (BUY, SELL), `quantity`, `price`, `date`.

5.  **quotes**
    *   Histórico de precios (OHLCV) para cada activo.
    *   `id` (UUID), `asset_id` (FK), `timestamp`, `close`, `open`, `high`, `low`, `volume`.
    *   **Índices**: Compuesto (`asset_id`, `timestamp`) para búsquedas rápidas de series temporales.

6.  **snapshots**
    *   Instantánea diaria del valor total de un portafolio. Calculado automáticamente.
    *   `id` (UUID), `portfolio_id` (FK), `date`, `total_value`, `cash_balance`, `invested_value`.

## 🔄 Migraciones con Alembic

Utilizamos **Alembic** para gestionar los cambios en el esquema de la base de datos de manera controlada y versionada.

### Comandos Comunes

**Crear una nueva migración** (después de modificar un modelo en `models/`):
```bash
# Desde la carpeta backend/
alembic revision --autogenerate -m "descripcion_del_cambio"
```

**Aplicar migraciones pendientes** (actualizar la BD):
```bash
alembic upgrade head
```

**Revertir la última migración**:
```bash
alembic downgrade -1
```

## 💾 Respaldo y Restauración

### Crear un Respaldo (Backup)

Usando `pg_dump` desde el contenedor de base de datos o externamente:

```bash
# Ejemplo usando Docker
docker exec -t bolsav2_db pg_dump -U postgres bolsav2 > backup_$(date +%Y%m%d).sql
```

### Restaurar un Respaldo

```bash
# Advertencia: Esto sobrescribirá los datos existentes
cat backup_file.sql | docker exec -i bolsav2_db psql -U postgres bolsav2
```

## 🔍 Notas de Rendimiento

- La tabla `quotes` puede crecer rápidamente. Se ha particionado lógicamente mediante índices para optimizar las consultas por rango de fechas.
- Los cálculos de `snapshots` se realizan en segundo plano para no bloquear la API principal durante importaciones masivas.
