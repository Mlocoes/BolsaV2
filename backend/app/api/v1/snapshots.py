"""
Portfolio Snapshots API endpoints
"""
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.auth import get_current_user, get_current_admin_user
from app.db.models import User
from app.db.session import get_db
from app.services.snapshot_service import snapshot_service
# from app.services.snapshot_scheduler import snapshot_scheduler

router = APIRouter()


# ============================================
# Snapshot Management Endpoints
# ============================================

@router.post("/create/{portfolio_id}")
async def create_snapshot(
    portfolio_id: UUID,
    target_date: date = Query(None, description="Date for snapshot (default: yesterday)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a snapshot for a specific portfolio and date
    
    Args:
        portfolio_id: Portfolio ID
        target_date: Date to create snapshot for (default: yesterday)
        
    Returns:
        Created snapshot summary
    """
    # Verify portfolio ownership (simplified - should check actual ownership)
    
    if not target_date:
        target_date = (datetime.now() - timedelta(days=1)).date()
    
    try:
        snapshot = await snapshot_service.create_snapshot(
            db,
            portfolio_id,
            target_date
        )
        
        return {
            "success": True,
            "snapshot_id": str(snapshot.id),
            "portfolio_id": str(portfolio_id),
            "date": target_date.isoformat(),
            "total_value": float(snapshot.total_value),
            "total_pnl": float(snapshot.total_pnl),
            "total_pnl_percent": float(snapshot.total_pnl_percent),
            "message": f"Snapshot created for {target_date}"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}"
        )


@router.post("/backfill/{portfolio_id}")
async def backfill_snapshots(
    portfolio_id: UUID,
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(None, description="End date (default: yesterday)"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Backfill historical snapshots for a portfolio
    
    Creates snapshots for all days in the date range.
    This can take some time for large ranges.
    
    Args:
        portfolio_id: Portfolio ID
        from_date: Start date
        to_date: End date (default: yesterday)
        
    Returns:
        Backfill summary
    """
    if not to_date:
        to_date = (datetime.now() - timedelta(days=1)).date()
    
    # Validate date range
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date must be before to_date"
        )
    
    days = (to_date - from_date).days + 1
    if days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum backfill range is 365 days"
        )
    
    try:
        result = await snapshot_service.create_daily_snapshots_for_portfolio(
            db,
            portfolio_id,
            from_date,
            to_date
        )
        
        return {
            "success": True,
            "portfolio_id": str(portfolio_id),
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "created": result["created"],
            "skipped": result["skipped"],
            "errors": result["errors"],
            "total_days": result["total_days"],
            "message": f"Backfill completed: {result['created']} snapshots created"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backfill failed: {str(e)}"
        )


# ============================================
# Snapshot Query Endpoints
# ============================================

@router.get("/dates/{portfolio_id}")
async def get_available_dates(
    portfolio_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all available snapshot dates for a portfolio
    
    Returns:
        List of dates with snapshot data available
    """
    try:
        from sqlalchemy import select, distinct
        from app.db.models_snapshots import PortfolioSnapshot
        
        result = await db.execute(
            select(distinct(PortfolioSnapshot.snapshot_date))
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioSnapshot.snapshot_date.desc())
        )
        dates = result.scalars().all()
        
        return {
            "success": True,
            "portfolio_id": str(portfolio_id),
            "dates": [d.isoformat() for d in dates],
            "count": len(dates)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dates: {str(e)}"
        )


@router.get("/history/{portfolio_id}")
async def get_snapshot_history(
    portfolio_id: UUID,
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(None, description="End date (default: today)"),
    include_positions: bool = Query(False, description="Include position details"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get snapshot history for a portfolio
    
    Returns daily snapshots for the specified date range.
    
    Args:
        portfolio_id: Portfolio ID
        from_date: Start date
        to_date: End date (default: today)
        include_positions: Include detailed position information
        
    Returns:
        List of snapshots
    """
    if not to_date:
        to_date = datetime.now().date()
    
    try:
        history = await snapshot_service.get_snapshot_history(
            db,
            portfolio_id,
            from_date,
            to_date,
            include_positions
        )
        
        return {
            "success": True,
            "portfolio_id": str(portfolio_id),
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "snapshots": history,
            "count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/latest/{portfolio_id}")
async def get_latest_snapshot(
    portfolio_id: UUID,
    include_positions: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the most recent snapshot for a portfolio
    
    Args:
        portfolio_id: Portfolio ID
        include_positions: Include position details
        
    Returns:
        Latest snapshot
    """
    try:
        # Get last 1 day of history
        today = datetime.now().date()
        history = await snapshot_service.get_snapshot_history(
            db,
            portfolio_id,
            today - timedelta(days=30),  # Look back 30 days to find most recent
            today,
            include_positions
        )
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No snapshots found for this portfolio"
            )
        
        return {
            "success": True,
            "portfolio_id": str(portfolio_id),
            "snapshot": history[-1]  # Most recent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve snapshot: {str(e)}"
        )


@router.get("/performance/{portfolio_id}")
async def get_performance_metrics(
    portfolio_id: UUID,
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y, ytd, all"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get performance metrics for a portfolio
    
    Args:
        portfolio_id: Portfolio ID
        period: Time period for metrics
        
    Returns:
        Performance metrics and statistics
    """
    # Calculate date range based on period
    today = datetime.now().date()
    
    if period == "7d":
        from_date = today - timedelta(days=7)
    elif period == "30d":
        from_date = today - timedelta(days=30)
    elif period == "90d":
        from_date = today - timedelta(days=90)
    elif period == "1y":
        from_date = today - timedelta(days=365)
    elif period == "ytd":
        from_date = date(today.year, 1, 1)
    else:  # all
        from_date = today - timedelta(days=365 * 3)  # 3 years max
    
    try:
        history = await snapshot_service.get_snapshot_history(
            db,
            portfolio_id,
            from_date,
            today,
            include_positions=False
        )
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No snapshots found for this portfolio"
            )
        
        # Calculate metrics
        first = history[0]
        last = history[-1]
        
        period_return = (
            (last["total_value"] - first["total_value"]) / first["total_value"] * 100
        ) if first["total_value"] > 0 else 0
        
        # Find best and worst days
        best_day = max(history, key=lambda x: x["daily_pnl_percent"])
        worst_day = min(history, key=lambda x: x["daily_pnl_percent"])
        
        # Calculate volatility (standard deviation of daily returns)
        daily_returns = [s["daily_pnl_percent"] for s in history if s["daily_pnl_percent"] != 0]
        if daily_returns:
            mean_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
            volatility = variance ** 0.5
        else:
            volatility = 0
        
        return {
            "success": True,
            "portfolio_id": str(portfolio_id),
            "period": period,
            "from_date": from_date.isoformat(),
            "to_date": today.isoformat(),
            "metrics": {
                "period_return": round(period_return, 2),
                "current_value": last["total_value"],
                "total_pnl": last["total_pnl"],
                "total_pnl_percent": round(last["total_pnl_percent"], 2),
                "best_day": {
                    "date": best_day["date"],
                    "return_percent": round(best_day["daily_pnl_percent"], 2)
                },
                "worst_day": {
                    "date": worst_day["date"],
                    "return_percent": round(worst_day["daily_pnl_percent"], 2)
                },
                "volatility": round(volatility, 2),
                "number_of_days": len(history)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate metrics: {str(e)}"
        )


# ============================================
# Scheduler Control Endpoints (Admin)
# ============================================

@router.get("/scheduler/status")
async def get_scheduler_status(
    _: User = Depends(get_current_admin_user),
):
    """
    Get snapshot scheduler status (Admin only)
    
    Returns:
        Scheduler status and configuration
    """
    return {
        "is_running": False,  # snapshot_scheduler.is_running,
        "run_time": "20:00",  # snapshot_scheduler.run_time.strftime("%H:%M"),
        "next_run": "Disabled"  # "Running daily" if snapshot_scheduler.is_running else "Stopped"
    }


@router.post("/scheduler/trigger")
async def trigger_snapshot_creation(
    target_date: date = Query(None, description="Date to create snapshots for"),
    background_tasks: BackgroundTasks = None,
    _: User = Depends(get_current_admin_user),
):
    """
    Manually trigger snapshot creation for all portfolios (Admin only)
    
    Args:
        target_date: Date to create snapshots for (default: yesterday)
        
    Returns:
        Trigger confirmation
    """
    # background_tasks.add_task(snapshot_scheduler.run_now, target_date)
    
    return {
        "success": False,
        "message": "Scheduler is disabled. Use manual snapshot creation endpoints instead",
        "target_date": (target_date or (datetime.now() - timedelta(days=1)).date()).isoformat()
    }