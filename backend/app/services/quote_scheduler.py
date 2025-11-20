"""
Scheduler automático para actualización de cotizaciones
"""
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.services.quote_service import QuoteService

logger = logging.getLogger(__name__)


class QuoteScheduler:
    """
    Scheduler para actualización automática de cotizaciones

    Ejecuta actualizaciones en intervalos configurables
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.update_interval_minutes = settings.QUOTE_UPDATE_INTERVAL_MINUTES

    async def update_all_quotes_job(self):
        """Job para actualizar todas las cotizaciones"""
        db = SessionLocal()
        try:
            logger.info("Iniciando actualización automática de cotizaciones")

            # Obtener todos los activos
            assets = db.query(Asset).all()

            if not assets:
                logger.info("No hay activos para actualizar")
                return

            quote_service = QuoteService(db)

            updated = 0
            failed = 0
            errors = []

            for asset in assets:
                try:
                    result = quote_service.update_latest_quote_realtime(asset.symbol)

                    if result and result.get("success"):
                        updated += 1
                        logger.debug(f"Actualizado {asset.symbol}: ${result.get('price')}")
                    else:
                        failed += 1
                        error_msg = result.get("error", "Unknown error") if result else "No response"
                        errors.append(f"{asset.symbol}: {error_msg}")
                        logger.warning(f"Fallo al actualizar {asset.symbol}: {error_msg}")

                    # Delay para respetar rate limits (60 llamadas/minuto = 1 por segundo)
                    await asyncio.sleep(1.1)

                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    errors.append(f"{asset.symbol}: {error_msg}")
                    logger.error(f"Error actualizando {asset.symbol}: {error_msg}")

            logger.info(
                f"Actualización completada: {updated} exitosas, {failed} fallidas "
                f"de {len(assets)} activos totales"
            )

            if errors:
                logger.warning(f"Errores encontrados: {len(errors)}")
                for error in errors[:5]:  # Log solo los primeros 5
                    logger.warning(f"  - {error}")

        except Exception as e:
            logger.error(f"Error en job de actualización: {str(e)}")
        finally:
            db.close()

    def start(self):
        """Iniciar el scheduler"""
        if self.is_running:
            logger.warning("Scheduler ya está corriendo")
            return

        if not settings.QUOTE_AUTO_UPDATE_ENABLED:
            logger.info("Actualizaciones automáticas desactivadas (QUOTE_AUTO_UPDATE_ENABLED=False)")
            return

        # Agregar job con trigger de intervalo
        self.scheduler.add_job(
            self.update_all_quotes_job,
            trigger=IntervalTrigger(minutes=self.update_interval_minutes),
            id='update_quotes',
            name='Actualización automática de cotizaciones',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True

        logger.info(
            f"Quote scheduler iniciado. "
            f"Intervalo de actualización: {self.update_interval_minutes} minutos"
        )

        # Calcular próxima ejecución
        next_run = datetime.now() + timedelta(minutes=self.update_interval_minutes)
        logger.info(f"Próxima actualización: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    def stop(self):
        """Detener el scheduler"""
        if not self.is_running:
            return

        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Quote scheduler detenido")

    async def trigger_update_now(self):
        """Ejecutar actualización manual inmediata"""
        logger.info("Actualización manual de cotizaciones activada")
        await self.update_all_quotes_job()

    def get_status(self) -> dict:
        """Obtener estado del scheduler"""
        next_run_time = None

        if self.is_running and self.scheduler.get_jobs():
            job = self.scheduler.get_job('update_quotes')
            if job and job.next_run_time:
                next_run_time = job.next_run_time.isoformat()

        return {
            "running": self.is_running,
            "enabled": settings.QUOTE_AUTO_UPDATE_ENABLED,
            "interval_minutes": self.update_interval_minutes,
            "next_run": next_run_time
        }

    def configure(self, update_interval_minutes: int):
        """
        Reconfigurar el intervalo de actualización

        Args:
            update_interval_minutes: Nuevo intervalo en minutos
        """
        self.update_interval_minutes = update_interval_minutes

        if self.is_running:
            # Reiniciar con nuevo intervalo
            self.stop()
            self.start()
            logger.info(f"Scheduler reconfigurado con intervalo de {update_interval_minutes} minutos")


# Instancia global del scheduler
quote_scheduler = QuoteScheduler()
