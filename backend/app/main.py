from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.session import session_manager
from app.routes import auth, portfolios, transactions, assets, prices, worker, quotes, import_export, users

app = FastAPI(
    title="BolsaV2",
    description="Sistema de Gestión de Carteras",
    version="2.0.0",
    redirect_slashes=False  # Desactivar redireccionamientos automáticos de barras finales
)

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    """Inicializar conexiones al arrancar"""
    await session_manager.connect()
    print("✓ Session manager conectado a Redis")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar"""
    await session_manager.disconnect()
    print("✓ Session manager desconectado")

# Configuración de CORS más permisiva para desarrollo
# Permite conexiones desde cualquier IP en la red local
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list if settings.ENVIRONMENT != "development" else [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.8:3000",
        "http://192.168.0.10:3000",
    ],  # En desarrollo, lista explícita de orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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

@app.get("/")
def root():
    return {"message": "BolsaV2 API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
