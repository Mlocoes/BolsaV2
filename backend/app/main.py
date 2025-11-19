from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import logging
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.session import session_manager
from app.routes import auth, portfolios, transactions, assets, prices, worker, quotes, import_export, users
from app.services.quote_scheduler import quote_scheduler
# from app.services.snapshot_scheduler import snapshot_scheduler
from app.api.v1 import snapshots

app = FastAPI(
    title="BolsaV2",
    description="Sistema de Gestión de Carteras",
    version="2.0.0",
    redirect_slashes=False  # Desactivar redireccionamientos automáticos de barras finales
)

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

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    """Inicializar conexiones y servicios al arrancar"""
    await session_manager.connect()
    print("✓ Session manager conectado a Redis")
    
    # Iniciar scheduler de cotizaciones
    try:
        quote_scheduler.start()
        print("✓ Quote scheduler iniciado")
    except Exception as e:
        print(f"⚠ Warning: Quote scheduler no pudo iniciar: {e}")
    
    # Iniciar scheduler de snapshots
    # try:
    #     import asyncio
    #     asyncio.create_task(snapshot_scheduler.run())
    #     print("✓ Snapshot scheduler iniciado")
    # except Exception as e:
    #     print(f"⚠ Warning: Snapshot scheduler no pudo iniciar: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones y servicios al apagar"""
    # Detener schedulers
    quote_scheduler.stop()
    print("✓ Quote scheduler detenido")
    
    # await snapshot_scheduler.stop()
    # print("✓ Snapshot scheduler detenido")
    
    await session_manager.disconnect()
    print("✓ Session manager desconectado")

# Configuración de CORS más permisiva para desarrollo
# Permite conexiones desde cualquier IP en la red local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.8:3000",
        "http://192.168.0.8:8000",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Session-ID",
    ],
    expose_headers=["Content-Disposition", "X-Session-ID"],
    max_age=3600,
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
