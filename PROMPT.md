Prompt para la implementación completa — BolsaV2
(Entrega: Backend Python + Docker, PostgreSQL, Frontend React con Handsontable, instalador, README y repo GitHub)
________________________________________
Objetivo (resumen)
Crear una aplicación multiusuario, robusta, segura y escalable llamada BolsaV2.
Tecnologías principales: Python (FastAPI), PostgreSQL, Docker / docker-compose, React (Vite) + Handsontable. Integración de cotizaciones mediante Finnhub Stock API (repo cliente: https://github.com/Finnhub-Stock-API/finnhub-python.git). Todo lo sensible en archivo .env. Entregar código listo, script de instalación y README. Inicializar repo https://github.com/Mlocoes/BolsaV2.git.
A continuación se especifica TODO lo requerido, en detalle técnico. Usa esto como prompt maestro para codificar el sistema.
________________________________________
1) Requerimientos funcionales y entregables
•	Especificar y entregar:
o	Esquema de la base de datos (DDL / migraciones Alembic).
o	Backend en Python (FastAPI) con Dockerfile y docker-compose.yml.
o	Frontend React (Vite) con Handsontable, responsive (desktop + móvil) y Dockerfile o servir por Nginx.
o	Archivo .env.example con todas las variables necesarias.
o	Script de instalación interactivo (install.sh) que:
	Solicita credenciales de admin y DB.
	Escribe .env.
	Verifica e instala dependencias (Python, Docker/Docker-compose, etc).
	Clona repo si falta.
	Crea la BD si no existe y ejecuta migraciones.
	Crea admin si no existe.
	Pregunta antes de cada acción.
o	README.md completo con instrucciones, arquitectura y comandos.
o	Inicializar repositorio Git, commitear y pushear al repo indicado.
o	Tests básicos (pytest) y GitHub Actions CI workflow que ejecuta lint y tests.
________________________________________
2) Base de datos — tablas y campos (PostgreSQL)
Diseña esquema con FK, índices y constraints. Usar UUIDs para ids.
1. users
•	id: UUID PK
•	username: varchar UNIQUE NOT NULL
•	email: varchar UNIQUE NOT NULL
•	password_hash: varchar NOT NULL (argon2/bcrypt)
•	is_admin: boolean NOT NULL DEFAULT false
•	active: boolean NOT NULL DEFAULT true
•	created_at, updated_at: timestamptz
•	last_login_at: timestamptz NULL
2. assets (valores: acciones, fondos, etc)
•	id: UUID PK
•	ticker: varchar UNIQUE NOT NULL
•	name: varchar
•	market: varchar (ej. NASDAQ)
•	asset_type: enum('stock','etf','fund','crypto', 'other')
•	created_at, updated_at
3. quotes (cotizaciones históricas / últimas)
•	id: UUID PK
•	asset_id: UUID FK -> assets.id
•	timestamp: timestamptz NOT NULL
•	open, high, low, close: numeric(18,6)
•	volume: bigint
•	source: varchar (ej. finnhub)
•	UNIQUE(asset_id, timestamp)
•	índice: (asset_id, timestamp DESC)
4. portfolios (carteras)
•	id: UUID PK
•	user_id: UUID FK -> users.id
•	name: varchar NOT NULL
•	description: text
•	created_at, updated_at
•	UNIQUE(user_id, name)
5. operations (operaciones dentro de carteras)
•	id: UUID PK
•	portfolio_id: UUID FK -> portfolios.id
•	date: date or timestamptz
•	asset_id: UUID FK -> assets.id
•	side: enum('buy','sell')
•	quantity: numeric(24,8)
•	price: numeric(18,6) — precio unitario
•	fee: numeric(18,6) NULLABLE
•	currency: varchar
•	notes: text
•	created_at, updated_at
•	índices: portfolio_id, asset_id
6. results (tablilla calculada o cache de resultados por cartera/mes/día)
•	id: UUID PK
•	portfolio_id: UUID FK
•	period_start: date
•	period_end: date
•	total_buy_amount: numeric
•	total_current_amount: numeric
•	pnl_absolute: numeric
•	pnl_percent: numeric
•	created_at, updated_at
•	índice: (portfolio_id, period_start)
Consideraciones DDL
•	FK con ON DELETE RESTRICT/SET NULL según caso.
•	Migraciones con Alembic.
•	Usar pgcrypto extension para gen_random_uuid() si se desea.
________________________________________
3) Backend — arquitectura y requerimientos
Stack sugerido: FastAPI (async), SQLAlchemy (1.4+/Core or ORM), Alembic, Pydantic, Uvicorn/Gunicorn for production, async DB driver asyncpg, conexion pool.
Estructura del proyecto (sugerida)
backend/
├─ app/
│  ├─ main.py
│  ├─ api/
│  │  ├─ v1/
│  │  │  ├─ auth.py
│  │  │  ├─ users.py
│  │  │  ├─ assets.py
│  │  │  ├─ quotes.py
│  │  │  ├─ portfolios.py
│  │  │  └─ imports.py
│  ├─ core/
│  │  ├─ config.py        # carga .env
│  │  ├─ security.py      # hashing, token helpers
│  │  └─ secrets_store.py # credenciales en memoria (ephemeral)
│  ├─ db/
│  │  ├─ models.py
│  │  ├─ session.py
│  │  └─ migrations/ (alembic)
│  ├─ services/
│  │  ├─ finnhub_client.py
│  │  ├─ quote_fetcher.py
│  │  └─ import_service.py
│  └─ tests/
API endpoints (REST JSON)
•	POST /api/v1/auth/login → body {username, password} → crea sesión efímera (token), devuelve token y expiry. (Sesiones guardadas en memoria del proceso; se invalidan al reiniciar el proceso).
•	POST /api/v1/auth/logout → invalida token.
•	GET /api/v1/users (admin) — CRUD usuarios: GET/POST/PUT/DELETE /api/v1/users/:id.
•	GET /api/v1/assets — listar/filtrar; POST/PUT/DELETE para catalogar assets (admin).
•	GET /api/v1/quotes/latest?asset_id= — recuperar última cotización.
•	POST /api/v1/quotes/import_historical — desencadena import histórico para una lista de assets (trabajo en background).
•	GET /api/v1/portfolios — lista carteras del usuario.
•	POST /api/v1/portfolios — crear cartera.
•	GET /api/v1/portfolios/{id}/positions — posiciones calculadas (unir operaciones + últimas cotizaciones).
•	POST /api/v1/operations/import_excel — subir Excel para importar operaciones a una cartera.
•	GET /api/v1/results/monthly — devuelve datos para gráfico mes a mes (suma de carteras del usuario).
Autenticación & sesiones
•	Implementar ephemeral server-side sessions:
o	Al login, generar token (crypto random string) y guardar en memoria del proceso en secrets_store junto con user_id y expiry (ej. 1h).
o	Todas las llamadas revisan token contra ese store.
o	La clave del requerimiento: las credenciales/sesiones son purgadas en reinicio (no persistir).
o	Documentar que para escalar usar Redis/Key-Value con TTL; implementa adaptador que ahora usa memoria, con posibilidad de switch a Redis.
•	Contraseñas: almacenar con argon2 o bcrypt (salting + pepper opcional). No almacenar contraseñas planas.
•	Todas las rutas protegidas deben validar token y permisos.
•	En endpoints críticos exigir re-autenticación (opcional).
Seguridad (must)
•	Validación y sanitización de inputs (Pydantic).
•	Queries parametrizadas / ORM.
•	Protección CSRF si usas cookies; preferir tokens en encabezado Authorization: Bearer.
•	Rate limiting por IP y por usuario (ejemplo: 100 req/min), implementable con middleware (in-memory o Redis).
•	Helmet-like headers, CORS whitelist configurable por ENV.
•	Escapar/limitar subida de archivos; tamaño máximo; escanear tipos (xlsx,csv).
•	Logging y auditoría (no loggear secrets).
•	Dependabot / seguridad en CI, escaneo de vulnerabilidades.
•	Revisar y mitigar OWASP Top 10: inyección, auth broken, XSS (en frontend), exposición de datos sin cifrar, etc.
Integración Finnhub
•	Servicio finnhub_client.py que utiliza repo finnhub-python para:
o	get_quote(ticker) (última)
o	get_historical(ticker, from,to) (import histórico)
•	API key en .env como FINNHUB_API_KEY.
•	Rate-limits: diseñar trabajo en background para respetar limites (throttling, backoff). Re-intentos controlados.
Import / background tasks
•	Para tareas largas (import histórico, procesar Excel), usar:
o	Variante simple: ejecutar tareas async + job queue con Redis + RQ/Celery (preferible) y worker en docker-compose.
o	Si se quiere simplicidad inicial: procesar en background thread + reportar estado; documentar limitaciones.
•	Endpoints deben devolver ID de job y estado.
Env vars (.env.example)
•	APP_ENV=production
•	SECRET_KEY=...
•	DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/bolsav2
•	FINNHUB_API_KEY=...
•	TOKEN_EXPIRY_MINUTES=60
•	CORS_ORIGINS=http://localhost:3000,https://mi-frontend.com
•	RATE_LIMIT=100/m
•	SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS (para notifs)
•	ADMIN_EMAIL, ADMIN_USERNAME (opcional)
•	REDIS_URL (opcional)
•	DOCKER related vars si aplica
Dev & Production
•	Configuración separada por entorno.
•	Gunicorn + Uvicorn workers para producción.
________________________________________
4) Frontend — requisitos
Stack: React + Vite, Typescript, Tailwind CSS (colores sobrios), Handsontable (licencia OSS o comercial según uso), Axios/fetch.
Estructura
frontend/
├─ src/
│  ├─ pages/
│  │  ├─ Login.tsx
│  │  ├─ Dashboard.tsx
│  │  ├─ AssetsCatalog.tsx
│  │  ├─ PortfoliosCatalog.tsx
│  │  ├─ UsersCatalog.tsx
│  │  └─ ImportData.tsx
│  ├─ components/
│  │  ├─ HandsontableWrapper.tsx
│  │  ├─ TopNav.tsx
│  │  └─ ChartMonthly.tsx
│  ├─ services/api.ts
│  └─ App.tsx
Requerimientos UI
•	Diseño empresarial, paleta sobria (grises, azul oscuro, acentos con un color suave).
•	Responsive: diseño grid que adapta a móvil.
•	Usar Handsontable para:
o	Mostrar posiciones (no editable).
o	Catastro de valores (editable).
o	Catastro de carteras y operaciones (editable).
•	Login: pantalla simple con username + password. Siempre que la app se recarga se debe pedir login: no persistir token en localStorage. Al recargar la página front-end debe abrir Login (para cumplir requerimiento). Sesión en memoria de la SPA (por ej. React state); al cerrar o recargar, se pierde y se redirige a Login.
•	Dashboard:
o	Lista de carteras del usuario.
o	Al click abrir posiciones en Handsontable no editable con columnas: nombre del valor, C/V, cantidad, precio de compra, último precio conocido, importe de compra, importe actual, resultado del día (abs y %), resultado acumulado (abs y %).
o	Gráfico mes a mes (all portfolios sumados) — usar Recharts o Chart.js.
•	Pantalla de import Excel: subir archivo, vista previa, botón importar.
•	UX: mostrar estados de jobs (import en progreso, terminado, error).
Seguridad en frontend
•	No guardar credenciales en localStorage.
•	Validación client-side + siempre validar server-side.
•	Mitigar XSS (escapar datos, evitar innerHTML).
________________________________________
5) Scripts, Docker y despliegue
Docker
•	backend/Dockerfile (user non-root, install deps, expose port 8000), use multi-stage build.
•	frontend/Dockerfile (build static + Nginx to serve or simple vite preview in prod).
•	docker-compose.yml con servicios:
o	db: image: postgres:15, volumes, env from .env
o	backend: build ./backend, env_file .env, depends_on db, ports
o	frontend: build ./frontend, env_file .env, ports
o	redis (opcional for tasks)
o	worker (opcional Celery/RQ worker)
o	pgadmin (opcional)
•	Volúmenes para persistencia DB.
•	Makefile with targets: build, up, down, migrate, create_admin, backup, restore.
Script de instalación (install.sh)
•	Interactivo:
1.	Pregunta si clonar repo si no existe.
2.	Pregunta datos DB (host, port, user, pass, dbname).
3.	Pregunta credenciales admin (username,email,password).
4.	Genera .env.
5.	Pregunta para instalar dependencias (opcional).
6.	Crea DB si no existe (usar psql o docker-compose run --rm backend alembic upgrade head).
7.	Ejecuta migraciones.
8.	Crea admin si no existe (script manage/create_admin.py).
9.	Inicia docker-compose up -d.
o	Antes de cada paso preguntar confirmación.
o	Validaciones de entrada.
•	Documentar que install.sh debe ser ejecutado en entorno con Docker instalado.
________________________________________
6) Pruebas, CI y calidad
•	Tests unitarios con pytest para backend (cobertura básica de modelos, servicios, endpoints críticos).
•	Linter: flake8/ruff, black formatting, isort.
•	Frontend: ESLint + Prettier, tests básicos (Jest + React Testing Library).
•	GitHub Actions:
o	Workflow ci.yml: on push PR -> run backend tests + lint, frontend build + lint.
o	Dependabot config (opcional).
________________________________________
7) Seguridad y mitigación de vulnerabilidades (resumen concreto)
•	No hardcodear secretos; .env único.
•	Principal mitigación: contraseñas hasheadas (argon2), rate limiting, input validation, escaping outputs.
•	Escaneo de dependencias (snyk/OSS).
•	HTTPS por TLS (documentar que en producción reverse-proxy o carga balance con certs debe manejar TLS).
•	Implementar Content Security Policy si se sirve frontend.
•	Logging de auditoría: operaciones CRUD sensibles, login attempts.
•	Backup plan: scripts para dump / restore de DB.
________________________________________
8) Integración y consideraciones de escalabilidad
•	DB: conexiones pool; índices en columnas de búsqueda.
•	Sesiones: por defecto en memoria (expiran on restart). Implementar abstracción para session store que pueda usarse con Redis para clustering.
•	Background jobs: implementar con Celery + Redis para tareas largas; workers autoscalables.
•	Stateless backend: no escribir en disco local; usar mounts / object storage para archivos.
________________________________________
9) Requerimientos operativos y criterios de aceptación
•	El sistema debe arrancar vía docker-compose up -d tras configurar .env.
•	Login funciona; token efímero en memoria y pierde validez si reinicias backend.
•	Se puede catalogar assets; se importan cotizaciones desde Finnhub (últimas e históricas) y se guardan en quotes.
•	Se puede crear carteras, operaciones (manual y desde Excel) y ver posiciones calculadas en Dashboard.
•	Tests unitarios pasan (pytest), linters pasan.
•	README explica:
o	Arquitectura, endpoints, ejemplos de requests, variables .env, instalador, comandos Docker, cómo crear admin y cómo migrar.
•	Repo inicializado y push al https://github.com/Mlocoes/BolsaV2.git (si la cuenta tiene permisos).
________________________________________
10) Entregables concretos al finalizar
1.	Repo Git con:
o	/backend (código, Dockerfile, alembic)
o	/frontend (código, Dockerfile)
o	docker-compose.yml, install.sh, Makefile, .env.example
o	README.md
o	.github/workflows/ci.yml
2.	Script install.sh funcional e interactivo.
3.	Documentación de seguridad y guía de deploy en producción.
4.	Archivo de ejemplo Excel para importación de operaciones.
5.	Tests automatizados y badges en README.
6.	Commit inicial y push al repo provisto.
________________________________________
11) Notas / restricciones importantes a incluir en la implementación
•	Nunca hardcodear credenciales o API keys en el código.
•	En la implementación inicial, las sesiones serán EN MEMORIA (cumpliendo el requisito: "Las credenciales deben ser perdidas en caso de recarga de la tela y nuevamente solicitadas"). Documentar limitación: no es horizontalmente escalable; se debe usar Redis para producción.
•	Priorizar seguridad por diseño: input validation, escaping, cifrado en tránsito y en reposo si aplica.
•	Finnhub: respetar rate-limits; implementar backoff.
________________________________________
12) Checklist para el desarrollador (acciones a realizar)
•	Inicializar repo con estructura propuesta.
•	Crear modelos SQLAlchemy y migraciones Alembic.
•	Implementar auth/session store in-memory con adaptador Redis posible.
•	Endpoints CRUD y servicios Finnhub.
•	Implementar job queue (preferible Celery + Redis).
•	Construir frontend con Handsontable y vistas solicitadas.
•	Tests y CI pipeline.
•	Dockerize everything y preparar docker-compose.
•	Implementar install.sh, Makefile.
•	Crear README y push al repo.
________________________________________
13) Ejemplo de prompt de entrada para una IA/DevOps (texto directo, listo para pegar)
Eres un desarrollador senior. Implementa el proyecto BolsaV2 exactamente según las especificaciones siguientes:
- Backend: FastAPI, async SQLAlchemy/asyncpg, Alembic, Docker. Autenticación con sesiones efímeras en memoria (tokens invalidables al reinicio). Hash de contraseñas con argon2. Integración con Finnhub (FINNHUB_API_KEY en .env). Endpoints REST v1 según especificaciones. Protecciones OWASP Top 10, rate-limiting, CORS, input validation. Job queue para import de cotizaciones y procesado de Excel (Celery+Redis preferible). Tests (pytest), linters (ruff/black).
- DB: PostgreSQL. Tablas: users, assets, quotes, portfolios, operations, results. UUID pks, índices y constraints.
- Frontend: React + Vite + Typescript + Tailwind + Handsontable. Pantallas: Login (siempre pide credenciales al recargar), Dashboard (carteras + posiciones + gráfico mensual), Catastro de Valores (editable), Catastro de Carteras (crear y editar operaciones), Catastro de Usuarios, Import Data (import histórico, últimas, Excel). Usar token-based auth en headers; no persistir token en localStorage (mantener en memoria SPA).
- Docker: Dockerfiles para backend y frontend, docker-compose con servicios db, backend, frontend, redis (opcional), worker (opcional).
- Scripts: install.sh interactivo que genera .env, crea BD, ejecuta migraciones, crea admin y levanta servicios; preguntar confirmación antes de cada paso.
- Documentar limitaciones y cómo escalar (Redis sessions, workers).
- Crear README y pushear al repo https://github.com/Mlocoes/BolsaV2.git

Entrega: todo el código en el repo, README detallado, tests pasando en CI. 
