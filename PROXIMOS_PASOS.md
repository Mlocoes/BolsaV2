# BolsaV2 - Próximos Pasos de Implementación

## Análisis de Estado Actual vs Requerimientos

### ✅ Ya Implementado

#### Backend
- ✅ FastAPI con estructura modular
- ✅ PostgreSQL con SQLAlchemy
- ✅ Modelos: Usuario, Portfolio, Asset, Position, Transaction
- ✅ Autenticación JWT básica
- ✅ Integración con Finnhub API para precios en tiempo real
- ✅ Endpoints CRUD para portfolios, assets, transactions
- ✅ Docker y docker-compose configurados
- ✅ Archivo .env para configuración

#### Frontend
- ✅ React 18 + TypeScript + Vite
- ✅ Tailwind CSS con diseño sobrio
- ✅ Login con autenticación
- ✅ Dashboard con portfolios y posiciones
- ✅ Gráficos de distribución y rendimiento (recharts)
- ✅ Modales para crear portfolios y transacciones
- ✅ Página de gestión de portfolios

---

## 🔴 Pendiente de Implementación

### 1. Base de Datos - Ajustes Críticos

#### 1.1 Migrar IDs a UUID
**Prioridad: ALTA**
- [ ] Cambiar todos los modelos de `Integer` a `UUID`
- [ ] Crear migración Alembic para convertir IDs existentes
- [ ] Actualizar todas las relaciones y foreign keys
- [ ] Actualizar schemas Pydantic para usar UUID

```python
# Ejemplo de cambio necesario en models
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

#### 1.2 Tabla de Cotizaciones (quotes)
**Prioridad: ALTA**
- [ ] Crear modelo `Quote` con campos:
  - id: UUID
  - asset_id: UUID FK
  - timestamp: timestamptz
  - open, high, low, close: Decimal(18,6)
  - volume: BigInteger
  - source: String (default: 'finnhub')
  - UNIQUE constraint (asset_id, timestamp)
- [ ] Crear índice compuesto: (asset_id, timestamp DESC)
- [ ] Migración Alembic

#### 1.3 Tabla de Resultados (results)
**Prioridad: MEDIA**
- [ ] Crear modelo `Result` para cache de P&L calculados:
  - id: UUID
  - portfolio_id: UUID FK
  - period_start: Date
  - period_end: Date
  - total_buy_amount: Decimal
  - total_current_amount: Decimal
  - pnl_absolute: Decimal
  - pnl_percent: Decimal
  - created_at, updated_at
- [ ] Índice: (portfolio_id, period_start)

#### 1.4 Campos Faltantes en Tablas Existentes
- [ ] **users**: agregar `last_login_at`, `active`
- [ ] **assets**: agregar `market` (ej: NASDAQ, NYSE)
- [ ] **operations/transactions**: agregar `currency` (USD, EUR, etc)

---

### 2. Backend - Features Críticas

#### 2.1 Sistema de Sesiones Efímeras (CRÍTICO)
**Prioridad: CRÍTICA**
- [ ] Implementar `secrets_store.py` con sesiones en memoria
- [ ] Reemplazar JWT por tokens efímeros:
  ```python
  class SessionStore:
      sessions = {}  # {token: {user_id, expiry, created_at}}
      
      def create_session(user_id, ttl=3600):
          token = secrets.token_urlsafe(32)
          sessions[token] = {...}
          return token
      
      def validate_session(token):
          # Check expiry, return user_id or None
  ```
- [ ] Endpoint `/api/v1/auth/logout` para invalidar sesión
- [ ] Middleware para validar token en cada request
- [ ] Cleanup automático de sesiones expiradas

#### 2.2 Import Histórico de Cotizaciones
**Prioridad: ALTA**
- [ ] Servicio `quote_fetcher.py`:
  ```python
  async def fetch_historical(ticker, from_date, to_date):
      # Usar Finnhub candles API
      # Guardar en tabla quotes
      # Rate limiting y retry logic
  ```
- [ ] Endpoint `POST /api/v1/quotes/import_historical`
- [ ] Background job con Celery/RQ:
  - Worker configurado en docker-compose
  - Redis para queue
  - Estado del job (pending, running, completed, failed)

#### 2.3 Import de Excel
**Prioridad: ALTA**
- [ ] Servicio `import_service.py`:
  - Parsear Excel (openpyxl)
  - Validar datos
  - Crear transacciones en batch
- [ ] Endpoint `POST /api/v1/operations/import_excel`
- [ ] Template Excel de ejemplo
- [ ] Validaciones:
  - Formato de fecha
  - Ticker existe en BD
  - Campos obligatorios

#### 2.4 Cálculo de Posiciones Mejorado
**Prioridad: MEDIA**
- [ ] Endpoint `GET /api/v1/portfolios/{id}/positions` con:
  - Resultado del día (cambio desde previous_close)
  - Resultado acumulado (vs precio promedio de compra)
  - Porcentajes calculados
- [ ] Cache en tabla `results` (opcional)

#### 2.5 Gestión de Usuarios (Admin)
**Prioridad: MEDIA**
- [ ] Endpoints CRUD `/api/v1/users`:
  - GET (lista, solo admin)
  - POST (crear, solo admin)
  - PUT (actualizar)
  - DELETE (solo admin)
- [ ] Middleware de permisos (check `is_admin`)

#### 2.6 Rate Limiting
**Prioridad: MEDIA**
- [ ] Implementar middleware de rate limiting:
  - Por IP: 100 req/min
  - Por usuario: límites configurables
  - Usar Redis o in-memory (simple dict con TTL)

#### 2.7 Seguridad Adicional
**Prioridad: ALTA**
- [ ] Migrar de bcrypt a argon2 para passwords
- [ ] CORS whitelist desde .env (ya implementado parcialmente)
- [ ] Headers de seguridad (Helmet-like):
  ```python
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  ```
- [ ] Logging de auditoría:
  - Login attempts
  - Operaciones CRUD sensibles
  - No loggear secrets

---

### 3. Frontend - Features Pendientes

#### 3.1 Sistema de Sesión No Persistente (CRÍTICO)
**Prioridad: CRÍTICA**
- [ ] Remover `sessionStorage` de token
- [ ] Guardar token solo en React state (Zustand)
- [ ] Al recargar página → redirigir a Login
- [ ] Event listener `beforeunload` para limpiar sesión

#### 3.2 Handsontable Integration
**Prioridad: ALTA**
- [ ] Instalar Handsontable: `npm install handsontable @handsontable/react`
- [ ] Componente `HandsontableWrapper.tsx`
- [ ] Reemplazar tablas en:
  - Dashboard posiciones (read-only)
  - Catálogo de valores (editable)
  - Catálogo de carteras/operaciones (editable)
  - Catálogo de usuarios (editable para admin)

#### 3.3 Catálogo de Valores (Assets)
**Prioridad: ALTA**
- [ ] Página `AssetsCatalog.tsx`:
  - Listar assets en Handsontable
  - Edición inline
  - Agregar/eliminar assets
  - Solo admin puede editar

#### 3.4 Catálogo de Usuarios
**Prioridad: MEDIA**
- [ ] Página `UsersCatalog.tsx` (solo admin):
  - Listar usuarios
  - Crear/editar/desactivar usuarios
  - Handsontable editable

#### 3.5 Importación de Datos
**Prioridad: ALTA**
- [ ] Página `ImportData.tsx`:
  - Botón "Importar Cotizaciones Históricas"
    - Selector de assets
    - Rango de fechas
    - Progress bar
  - Botón "Actualizar Últimas Cotizaciones"
    - Import batch de todos los assets
  - Botón "Importar Excel de Operaciones"
    - File upload
    - Vista previa de datos
    - Validación
    - Importar a portfolio seleccionado

#### 3.6 Dashboard Mejorado
**Prioridad: MEDIA**
- [ ] Mostrar "Resultado del Día" por posición
- [ ] Gráfico mes a mes de todas las carteras sumadas
- [ ] Filtros por fecha

#### 3.7 UX/UI Improvements
**Prioridad: MEDIA**
- [ ] Toast notifications para operaciones
- [ ] Confirmación antes de eliminar
- [ ] Estados de loading más robustos
- [ ] Error boundaries
- [ ] Modo oscuro (opcional)

---

### 4. DevOps y Deployment

#### 4.1 Script de Instalación Interactivo
**Prioridad: ALTA**
- [ ] Crear `install.sh` con:
  ```bash
  #!/bin/bash
  # 1. Verificar dependencias (docker, docker-compose, psql)
  # 2. Clonar repo si no existe
  # 3. Pedir credenciales:
  #    - DB (host, port, user, pass, dbname)
  #    - Admin (username, email, password)
  #    - Finnhub API key
  # 4. Generar .env
  # 5. Crear BD si no existe
  # 6. Ejecutar migraciones (alembic upgrade head)
  # 7. Crear usuario admin
  # 8. docker-compose up -d
  # IMPORTANTE: preguntar confirmación antes de cada paso
  ```

#### 4.2 Makefile
**Prioridad: MEDIA**
- [ ] Crear `Makefile` con targets:
  ```makefile
  build: docker-compose build
  up: docker-compose up -d
  down: docker-compose down
  migrate: docker-compose run --rm backend alembic upgrade head
  create_admin: docker-compose run --rm backend python scripts/create_admin.py
  backup: pg_dump...
  restore: psql...
  test: pytest
  lint: ruff check && black --check
  ```

#### 4.3 Celery Worker (Background Jobs)
**Prioridad: ALTA**
- [ ] Configurar Celery en `backend/app/worker.py`
- [ ] Redis service en docker-compose
- [ ] Worker service en docker-compose:
  ```yaml
  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    depends_on:
      - redis
      - db
    env_file: .env
  ```
- [ ] Tasks para:
  - Import histórico
  - Import de Excel
  - Actualización de cotizaciones

#### 4.4 CI/CD
**Prioridad: MEDIA**
- [ ] GitHub Actions `.github/workflows/ci.yml`:
  ```yaml
  name: CI
  on: [push, pull_request]
  jobs:
    backend:
      - lint (ruff, black)
      - test (pytest)
    frontend:
      - lint (eslint)
      - build (tsc && vite build)
  ```
- [ ] Dependabot config

#### 4.5 Tests
**Prioridad: MEDIA**
- [ ] Backend tests con pytest:
  - Test de modelos
  - Test de endpoints
  - Test de servicios (Finnhub mock)
  - Test de autenticación
- [ ] Frontend tests:
  - Test de componentes (Jest + React Testing Library)
  - Test de servicios API

---

### 5. Documentación

#### 5.1 README.md Completo
**Prioridad: ALTA**
- [ ] Arquitectura del sistema
- [ ] Requisitos y dependencias
- [ ] Instalación con `install.sh`
- [ ] Comandos Docker
- [ ] Variables de entorno (.env.example)
- [ ] Endpoints API (con ejemplos curl)
- [ ] Cómo crear usuario admin
- [ ] Cómo ejecutar migraciones
- [ ] Troubleshooting

#### 5.2 Documentación de API
**Prioridad: MEDIA**
- [ ] Swagger/OpenAPI automático (FastAPI ya lo genera)
- [ ] Ejemplos de requests/responses
- [ ] Códigos de error

#### 5.3 Guía de Seguridad
**Prioridad: MEDIA**
- [ ] Documento `SECURITY.md` con:
  - Limitaciones de sesiones in-memory
  - Cómo escalar con Redis
  - Best practices
  - OWASP Top 10 mitigation

---

## 📋 Plan de Ejecución Sugerido

### Sprint 1: Fundaciones Críticas (Semana 1)
1. ✅ Migrar IDs a UUID
2. ✅ Implementar sesiones efímeras en memoria
3. ✅ Tabla de quotes y servicio de import histórico
4. ✅ Configurar Celery + Redis + Worker

### Sprint 2: Import y Gestión (Semana 2)
5. ✅ Import de Excel de operaciones
6. ✅ Endpoints de gestión de usuarios (admin)
7. ✅ Rate limiting y seguridad adicional
8. ✅ Handsontable en frontend

### Sprint 3: Catálogos y UI (Semana 3)
9. ✅ Página de Catálogo de Valores
10. ✅ Página de Catálogo de Usuarios
11. ✅ Página de Importación de Datos
12. ✅ Dashboard mejorado con resultado del día

### Sprint 4: DevOps y Finalización (Semana 4)
13. ✅ Script install.sh interactivo
14. ✅ Makefile
15. ✅ Tests (backend y frontend)
16. ✅ CI/CD (GitHub Actions)
17. ✅ README y documentación completa

---

## 🎯 Criterios de Aceptación Final

### Backend
- [ ] Todas las tablas especificadas creadas con UUIDs
- [ ] Sesiones efímeras funcionando (pierden validez al reiniciar)
- [ ] Import de cotizaciones históricas funcional
- [ ] Import de Excel funcional
- [ ] Background jobs con Celery
- [ ] Rate limiting implementado
- [ ] Tests unitarios pasando
- [ ] Linters pasando (ruff, black)

### Frontend
- [ ] Login no persiste token (pide credenciales al recargar)
- [ ] Handsontable integrado en todas las vistas
- [ ] Todas las páginas implementadas:
  - Login ✅
  - Dashboard ✅ (falta resultado del día)
  - Catálogo de Valores ❌
  - Catálogo de Carteras ✅
  - Catálogo de Usuarios ❌
  - Importación de Datos ❌
- [ ] Diseño responsivo (desktop + móvil)
- [ ] Tests básicos pasando

### DevOps
- [ ] Docker-compose funcional con todos los servicios
- [ ] Script install.sh interactivo y funcional
- [ ] Makefile con comandos útiles
- [ ] CI/CD configurado
- [ ] README completo

### Seguridad
- [ ] Passwords con argon2
- [ ] CORS configurado
- [ ] Headers de seguridad
- [ ] Input validation
- [ ] Logging de auditoría
- [ ] Rate limiting

---

## 📝 Notas Importantes

1. **Sesiones Efímeras**: Esta es la característica más crítica que falta. Debe implementarse antes de cualquier otra feature.

2. **UUIDs**: La migración a UUID es fundamental para el esquema de BD especificado. Debe hacerse temprano.

3. **Handsontable**: Licencia necesaria si es uso comercial. Verificar antes de implementar.

4. **Finnhub Rate Limits**: 
   - Free tier: 60 calls/min
   - Implementar throttling y retry logic

5. **Background Jobs**: Necesario para imports largos. No bloquear requests HTTP.

6. **Escalabilidad**: Documentar limitaciones de in-memory sessions y path a Redis.

---

## 🔗 Referencias

- PROMPT.md - Especificaciones completas
- IDEIA.md - Visión original del proyecto
- Finnhub API: https://finnhub.io/docs/api
- Handsontable: https://handsontable.com/docs/
