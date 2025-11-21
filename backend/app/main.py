from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.gzip import GZipMiddleware
import logging
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.session import session_manager
from app.routes import auth, portfolios, transactions, assets, prices, worker, quotes, import_export, users
from app.services.quote_scheduler import quote_scheduler
# from app.services.snapshot_scheduler import snapshot_scheduler
from app.api.v1 import snapshots

# Configurar rate limiter global
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="BolsaV2",
    description="Sistema de Gestión de Carteras",
    version="2.0.0",
    redirect_slashes=False  # Desactivar redireccionamientos automáticos de barras finales
)

# Agregar state de slowapi para rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar logging básico
logger = logging.getLogger("bolsav2")
logging.basicConfig(level=logging.INFO)

# Manejo de excepciones
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
        },
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Ocurrió un error interno. Inténtalo nuevamente más tarde.",
        },
    )

# Middleware de seguridad - Headers HTTP
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Agregar headers de seguridad HTTP"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Middleware de compresión gzip
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    """Inicializar conexiones y servicios al arrancar"""
    await session_manager.connect()
    logger.info("✓ Session manager conectado a Redis")
    
    # Iniciar scheduler de cotizaciones
    try:
        quote_scheduler.start()
        logger.info("✓ Quote scheduler iniciado")
    except Exception as e:
        logger.warning(f"⚠ Quote scheduler no pudo iniciar: {e}")
    
    # Iniciar scheduler de snapshots
    try:
        import asyncio
        from app.services.snapshot_scheduler import snapshot_scheduler
        asyncio.create_task(snapshot_scheduler.run())
        logger.info("✓ Snapshot scheduler iniciado - creará snapshots automáticamente cada día")
    except Exception as e:
        logger.warning(f"⚠ Snapshot scheduler no pudo iniciar: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones y servicios al apagar"""
    # Detener schedulers
    quote_scheduler.stop()
    logger.info("✓ Quote scheduler detenido")
    
    # await snapshot_scheduler.stop()
    # print("✓ Snapshot scheduler detenido")
    
    await session_manager.disconnect()
    logger.info("✓ Session manager desconectado")

# CORS: Permitir frontend local y red local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.8:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Incluir rutas
app.include_router(auth.router)
app.include_router(portfolios.router)
app.include_router(transactions.router)
app.include_router(assets.router)
app.include_router(prices.router)
app.include_router(worker.router)
app.include_router(quotes.router)
app.include_router(import_export.router)
app.include_router(users.router)
app.include_router(snapshots.router, prefix="/api/v1/snapshots", tags=["snapshots"])

@app.get("/")
def root():
    return {"message": "BolsaV2 API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
