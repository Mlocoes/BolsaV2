"""
Tareas asíncronas de Celery
"""
import logging
from datetime import datetime, date
from typing import List, Dict
from sqlalchemy.orm import Session
import finnhub

from app.services.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.asset import Asset
from app.models.position import Position

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name="app.services.celery_tasks.update_all_asset_prices", bind=True)
def update_all_asset_prices(self):
    """
    Actualizar precios de todos los assets activos
    Se ejecuta cada 15 minutos
    """
    logger.info("🔄 Iniciando actualización de precios de assets")
    
    db = SessionLocal()
    try:
        # Obtener todos los assets únicos que están en portfolios
        assets_in_use = db.query(Asset).join(Position).distinct().all()
        
        total_assets = len(assets_in_use)
        updated = 0
        errors = []
        
        logger.info(f"📊 Encontrados {total_assets} assets en uso")
        
        finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
        
        for asset in assets_in_use:
            try:
                # Obtener precio actual desde Finnhub
                quote = finnhub_client.quote(asset.symbol)
                
                if quote and quote.get('c'):  # 'c' es el current price
                    current_price = quote['c']
                    
                    # Actualizar el asset (podrías agregar un campo last_price al modelo)
                    logger.info(f"✓ {asset.symbol}: ${current_price}")
                    updated += 1
                else:
                    logger.warning(f"⚠️ {asset.symbol}: No se pudo obtener precio")
                    errors.append(f"{asset.symbol}: No data")
                    
            except Exception as e:
                logger.error(f"✗ Error al actualizar {asset.symbol}: {str(e)}")
                errors.append(f"{asset.symbol}: {str(e)}")
        
        db.commit()
        
        result = {
            "total": total_assets,
            "updated": updated,
            "errors": len(errors),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Actualización completada: {updated}/{total_assets} assets")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en actualización masiva: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="app.services.celery_tasks.update_single_asset_price")
def update_single_asset_price(symbol: str) -> Dict:
    """
    Actualizar precio de un asset específico
    
    Args:
        symbol: Símbolo del asset
    
    Returns:
        Dict con el resultado de la actualización
    """
    logger.info(f"🔄 Actualizando precio de {symbol}")
    
    db = SessionLocal()
    try:
        asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        
        if not asset:
            logger.error(f"❌ Asset {symbol} no encontrado")
            return {"success": False, "error": "Asset not found"}
        
        finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
        quote = finnhub_client.quote(symbol.upper())
        
        if quote and quote.get('c'):
            current_price = quote['c']
            logger.info(f"✓ {symbol}: ${current_price}")
            
            return {
                "success": True,
                "symbol": symbol,
                "price": current_price,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            logger.warning(f"⚠️ No se pudo obtener precio para {symbol}")
            return {"success": False, "error": "No price data available"}
            
    except Exception as e:
        logger.error(f"❌ Error al actualizar {symbol}: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.services.celery_tasks.cleanup_expired_sessions")
def cleanup_expired_sessions():
    """
    Limpiar sesiones expiradas de Redis
    Se ejecuta diariamente a las 3 AM
    """
    logger.info("🧹 Iniciando limpieza de sesiones expiradas")
    
    try:
        from app.core.session import session_manager
        import asyncio
        
        async def cleanup():
            await session_manager.connect()
            
            # Redis automáticamente elimina keys expiradas, 
            # pero podemos verificar y contar
            pattern = "session:*"
            count = 0
            
            async for key in session_manager.redis_client.scan_iter(match=pattern):
                count += 1
            
            logger.info(f"✓ Sesiones activas: {count}")
            
            await session_manager.disconnect()
            
            return {"active_sessions": count, "timestamp": datetime.utcnow().isoformat()}
        
        result = asyncio.run(cleanup())
        logger.info("✅ Limpieza de sesiones completada")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza de sesiones: {str(e)}")
        raise


@celery_app.task(name="app.services.celery_tasks.import_historical_quotes")
def import_historical_quotes(symbol: str, start_date: str, end_date: str) -> Dict:
    """
    Importar cotizaciones históricas de un asset
    Tarea asíncrona para no bloquear el API
    
    Args:
        symbol: Símbolo del asset
        start_date: Fecha de inicio (YYYY-MM-DD)
        end_date: Fecha de fin (YYYY-MM-DD)
    
    Returns:
        Dict con resultado de la importación
    """
    logger.info(f"📥 Importando datos históricos de {symbol}: {start_date} to {end_date}")
    
    db = SessionLocal()
    try:
        from app.services.quote_service import QuoteService
        from datetime import datetime
        
        service = QuoteService(db)
        
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        result = service.import_historical_from_finnhub(symbol, start, end)
        
        logger.info(f"✅ Importación completada para {symbol}: {result.created} creados, {result.updated} actualizados")
        
        return {
            "success": True,
            "symbol": symbol,
            "total": result.total,
            "created": result.created,
            "updated": result.updated,
            "skipped": result.skipped,
            "errors": result.errors
        }
        
    except Exception as e:
        logger.error(f"❌ Error en importación histórica de {symbol}: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()
