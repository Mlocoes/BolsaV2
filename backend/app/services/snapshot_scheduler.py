"""
Automatic daily snapshot scheduler
"""
import asyncio
import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.db.models import Portfolio
from app.services.snapshot_service import snapshot_service

logger = logging.getLogger(__name__)


class SnapshotScheduler:
    """
    Scheduler for automatic daily portfolio snapshots
    
    Runs at end of each trading day to capture portfolio state
    """
    
    def __init__(self, run_time: time = time(hour=20, minute=0)):
        """
        Initialize scheduler
        
        Args:
            run_time: Time to run daily snapshots (default: 20:00 / 8 PM)
        """
        self.run_time = run_time
        self.is_running = False
        self.engine = None
        self.SessionLocal = None
        
    def initialize(self):
        """Initialize database connection"""
        self.engine = create_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )
        
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=Session,
            expire_on_commit=False
        )
        
        logger.info("Snapshot scheduler initialized")
    
    async def create_snapshots_job(self, target_date: date = None):
        """
        Job to create snapshots for all portfolios
        
        Args:
            target_date: Date to create snapshots for (default: yesterday)
        """
        if not self.SessionLocal:
            logger.error("Scheduler not initialized")
            return
        
        if not target_date:
            # Use yesterday (market close)
            target_date = (datetime.now() - timedelta(days=1)).date()

        with self.SessionLocal() as session:
            try:
                # Get all active portfolios
                result = session.execute(select(Portfolio))
                portfolios = result.scalars().all()
                
                if not portfolios:
                    logger.info("No portfolios found for snapshot creation")
                    return

                logger.info(
                    f"Starting snapshot creation for {len(portfolios)} portfolios "
                    f"for date {target_date}"
                )
                
                created = 0
                skipped = 0
                errors = []

                for portfolio in portfolios:
                    try:
                        snapshot_service.create_snapshot(
                            session,
                            portfolio.id,
                            target_date
                        )
                        created += 1
                        logger.info(f"Created snapshot for portfolio {portfolio.name}")
                        
                    except ValueError:
                        # Snapshot already exists
                        skipped += 1
                        logger.debug(f"Snapshot already exists for portfolio {portfolio.name}")
                        
                    except Exception as e:
                        errors.append({
                            "portfolio_id": str(portfolio.id),
                            "portfolio_name": portfolio.name,
                            "error": str(e)
                        })
                        logger.error(
                            f"Failed to create snapshot for portfolio {portfolio.name}: {str(e)}"
                        )

                logger.info(
                    f"Snapshot creation completed: "
                    f"{created} created, {skipped} skipped, {len(errors)} errors"
                )
                
                if errors:
                    for error in errors:
                        logger.error(
                            f"Portfolio {error['portfolio_name']}: {error['error']}"
                        )

            except Exception as e:
                logger.error(f"Error in snapshot creation job: {str(e)}")
    
    async def wait_until_next_run(self):
        """Calculate and wait until next scheduled run"""
        now = datetime.now()
        next_run = datetime.combine(now.date(), self.run_time)
        
        # If time has passed today, schedule for tomorrow
        if now >= next_run:
            next_run += timedelta(days=1)
        
        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"Next snapshot creation at {next_run} ({wait_seconds/3600:.1f} hours)")
        
        await asyncio.sleep(wait_seconds)
    
    async def run(self):
        """
        Run the scheduler
        
        This method runs indefinitely and creates snapshots daily
        """
        self.initialize()
        self.is_running = True
        
        logger.info(
            f"Snapshot scheduler started. "
            f"Daily run time: {self.run_time.strftime('%H:%M')}"
        )
        
        while self.is_running:
            try:
                # Wait until scheduled time
                await self.wait_until_next_run()
                
                # Run snapshot creation
                await self.create_snapshots_job()
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                # Wait a bit before retrying
                await asyncio.sleep(300)  # 5 minutes
    
    async def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping snapshot scheduler")
        self.is_running = False
        
        if self.engine:
            self.engine.dispose()
    
    async def run_now(self, target_date: date = None):
        """
        Manually trigger snapshot creation
        
        Args:
            target_date: Date to create snapshots for
        """
        logger.info(f"Manual snapshot creation triggered for {target_date or 'yesterday'}")
        await self.create_snapshots_job(target_date)
    
    async def backfill_snapshots(
        self,
        portfolio_id: str = None,
        from_date: date = None,
        to_date: date = None
    ):
        """
        Backfill historical snapshots
        
        Args:
            portfolio_id: Specific portfolio ID (None = all)
            from_date: Start date (None = 30 days ago)
            to_date: End date (None = yesterday)
        """
        if not self.SessionLocal:
            self.initialize()

        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).date()
        
        if not to_date:
            to_date = (datetime.now() - timedelta(days=1)).date()

        with self.SessionLocal() as session:
            if portfolio_id:
                # Backfill specific portfolio
                logger.info(
                    f"Backfilling snapshots for portfolio {portfolio_id} "
                    f"from {from_date} to {to_date}"
                )
                
                result = snapshot_service.create_daily_snapshots_for_portfolio(
                    session,
                    portfolio_id,
                    from_date,
                    to_date
                )
                
                logger.info(
                    f"Backfill completed: {result['created']} created, "
                    f"{result['skipped']} skipped"
                )
                
            else:
                # Backfill all portfolios
                result = session.execute(select(Portfolio))
                portfolios = result.scalars().all()
                
                logger.info(
                    f"Backfilling snapshots for {len(portfolios)} portfolios "
                    f"from {from_date} to {to_date}"
                )
                
                total_created = 0
                total_skipped = 0
                
                for portfolio in portfolios:
                    result = snapshot_service.create_daily_snapshots_for_portfolio(
                        session,
                        portfolio.id,
                        from_date,
                        to_date
                    )
                    total_created += result['created']
                    total_skipped += result['skipped']
                    
                    logger.info(
                        f"Portfolio {portfolio.name}: "
                        f"{result['created']} created, {result['skipped']} skipped"
                    )
                
                logger.info(
                    f"Total backfill: {total_created} created, {total_skipped} skipped"
                )


# Global scheduler instance
# Runs daily at 8 PM (after market close)
snapshot_scheduler = SnapshotScheduler(run_time=time(hour=20, minute=0))


async def start_snapshot_scheduler():
    """Start the snapshot scheduler in background"""
    await snapshot_scheduler.run()


async def stop_snapshot_scheduler():
    """Stop the snapshot scheduler"""
    await snapshot_scheduler.stop()
    await snapshot_scheduler.stop()