import asyncio
import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models.order import Order
from app.models.service import Service
from app.models.task_log import TaskLog
from app.services.device_pool import get_device_pool_size
from app.services.view_booster import manager, run_campaign_in_thread, run_view_booster_campaign

router = APIRouter(prefix="/view-booster", tags=["Facebook Views & Reach Booster"])


class LaunchViewBoostRequest(BaseModel):
    post_url: str = Field(..., example="https://www.facebook.com/reel/1767246594345288")
    quantity: int = Field(default=50, ge=1, le=500, description="Total views & impressions to deliver (1-500)")
    dwell_seconds: float = Field(default=15.0, ge=3.0, le=60.0, description="Dwell retention time per view in seconds (up to 60s)")
    concurrency: int = Field(default=4, ge=1, le=10, description="Number of parallel Playwright browser workers")


async def _run_background_view_campaign(task_id: str, order_id: str, post_url: str, quantity: int, dwell_seconds: float, concurrency: int):
    """Background task runner that executes Playwright in a dedicated thread and updates TiDB Cloud database."""
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        run_campaign_in_thread,
        task_id,
        post_url,
        quantity,
        dwell_seconds,
        concurrency
    )

    # Persist final state in TiDB Cloud
    try:
        async with AsyncSessionLocal() as db:
            order = await db.get(Order, order_id)
            if order:
                order.delivered_count = result.get("delivered", 0)
                order.remains_count = max(0, order.quantity - order.delivered_count)
                order.status = "Completed" if order.remains_count == 0 else "Partial"

                # Save individual task logs
                for log in result.get("logs", []):
                    task_log = TaskLog(
                        order_id=order.id,
                        persona_id=None,
                        action_type="view",
                        status="SUCCESS" if log["status"] == "SUCCESS" else "FAILED",
                        execution_time_ms=int(log.get("dwell_seconds", 0) * 1000),
                        details=f"{log.get('device')} ({log.get('viewport')}) | Ref: {log.get('referrer')} | {log.get('message')}"
                    )
                    db.add(task_log)

                await db.commit()
    except Exception as e:
        print(f"Failed to update Order in TiDB Cloud: {e}")


@router.post("/launch", status_code=status.HTTP_201_CREATED)
async def launch_view_boost(payload: LaunchViewBoostRequest, db: AsyncSession = Depends(get_db)):
    """Launch real Playwright headless browser views & impressions on a Facebook post/video/reel."""
    # Find service ID for views
    srv_res = await db.execute(select(Service).where(Service.service_type == "view").limit(1))
    srv = srv_res.scalars().first()
    service_id = srv.id if srv else 3

    task_id = str(uuid.uuid4())
    order_id = str(uuid.uuid4())

    new_order = Order(
        id=order_id,
        service_id=service_id,
        target_url=payload.post_url,
        quantity=payload.quantity,
        delivered_count=0,
        remains_count=payload.quantity,
        status="In progress",
        drip_feed=False,
        interval_seconds=int(payload.dwell_seconds)
    )
    db.add(new_order)
    await db.commit()

    # Launch non-blocking background workers
    asyncio.create_task(
        _run_background_view_campaign(
            task_id=task_id,
            order_id=order_id,
            post_url=payload.post_url,
            quantity=payload.quantity,
            dwell_seconds=payload.dwell_seconds,
            concurrency=payload.concurrency
        )
    )

    return {
        "success": True,
        "task_id": task_id,
        "order_id": order_id,
        "target_url": payload.post_url,
        "quantity": payload.quantity,
        "dwell_seconds": payload.dwell_seconds,
        "concurrency": payload.concurrency,
        "message": f"Real View & Reach Booster launched with {payload.concurrency} parallel browser workers!"
    }


@router.get("/status/{task_id}")
async def get_view_boost_status(task_id: str):
    """Get live real-time progress and logs of an active view boost campaign."""
    task = manager.get_task(task_id)
    if not task:
        # Check database if task is already archived
        return {
            "task_id": task_id,
            "status": "NOT_FOUND_OR_ARCHIVED",
            "delivered": 0,
            "total_requested": 0,
            "logs": []
        }

    return task


@router.get("/pool-info")
async def get_device_pool_info():
    """Return total number of unique realistic device fingerprints available in the pool."""
    return {
        "total_unique_devices": get_device_pool_size(),
        "stealth_evasion": "Enabled (navigator.webdriver bypass, WebGL spoofing, random bezier mouse/scroll jitters)",
        "max_dwell_seconds": 60.0
    }

