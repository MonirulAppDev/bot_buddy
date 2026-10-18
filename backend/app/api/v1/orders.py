import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.order import Order
from app.models.service import Service
from app.models.task_log import TaskLog
from app.schemas.order import OrderCreate, OrderResponse
from app.services.simulation_engine import process_order_simulation

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=dict)
async def list_orders(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None
):
    """List engagement orders with pagination and filtering."""
    query = select(Order).options(selectinload(Order.service))
    if status:
        query = query.where(Order.status == status)

    total = await db.scalar(select(func.count(Order.id)))
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(Order.created_at.desc()).offset(offset).limit(limit))
    items = result.scalars().all()

    return {
        "items": [OrderResponse.model_validate(o) for o in items],
        "total": total or 0,
        "page": page,
        "limit": limit
    }


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new dummy social media engagement order and begin async execution."""
    service = await db.get(Service, payload.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if payload.quantity < service.min_quantity or payload.quantity > service.max_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Quantity must be between {service.min_quantity} and {service.max_quantity}"
        )

    order_id = str(uuid.uuid4())
    order = Order(
        id=order_id,
        service_id=payload.service_id,
        target_url=payload.target_url,
        quantity=payload.quantity,
        delivered_count=0,
        remains_count=payload.quantity,
        status="Pending",
        comments=payload.comments,
        drip_feed=payload.drip_feed,
        interval_seconds=payload.interval_seconds or service.default_interval_seconds,
        runs=payload.runs
    )

    db.add(order)
    await db.commit()
    await db.refresh(order, attribute_names=["service"])

    # Trigger background delivery simulation
    background_tasks.add_task(process_order_simulation, order_id)

    return OrderResponse.model_validate(order)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Get single order status and live progress."""
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.service))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.model_validate(order)


@router.get("/{order_id}/logs")
async def get_order_task_logs(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200)
):
    """Retrieve detailed execution audit logs for an order."""
    result = await db.execute(
        select(TaskLog)
        .where(TaskLog.order_id == order_id)
        .order_by(TaskLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "action_type": log.action_type,
            "status": log.status,
            "execution_time_ms": log.execution_time_ms,
            "details": log.details,
            "created_at": log.created_at
        }
        for log in logs
    ]
