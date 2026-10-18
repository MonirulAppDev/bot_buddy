import uuid
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.order import Order
from app.models.service import Service
from app.services.simulation_engine import process_order_simulation

router = APIRouter(prefix="/api/v2", tags=["SMM Standard API v2"])


@router.api_route("", methods=["GET", "POST"])
async def smm_v2_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Industry-standard SMM API v2 endpoint compatible with all SMM panels and automation tools."""
    # SMM panels usually post form data, but sometimes use query parameters or JSON
    data = {}
    if request.method == "POST":
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            try:
                data = await request.json()
            except Exception:
                pass
    
    if not data:
        data = dict(request.query_params)

    action = data.get("action")
    if not action:
        return {"error": "Incorrect request: 'action' parameter is required"}

    # 1. ACTION: services
    if action == "services":
        result = await db.execute(select(Service).where(Service.is_active == True))
        services = result.scalars().all()
        return [
            {
                "service": s.id,
                "name": s.name,
                "type": "Default",
                "category": f"{s.platform.capitalize()} Engagement",
                "rate": str(s.rate_per_1000),
                "min": str(s.min_quantity),
                "max": str(s.max_quantity),
                "dripfeed": True,
                "refill": False,
                "cancel": False
            }
            for s in services
        ]

    # 2. ACTION: balance
    elif action == "balance":
        return {
            "balance": f"{settings.MOCK_BALANCE:.2f}",
            "currency": settings.MOCK_CURRENCY
        }

    # 3. ACTION: add
    elif action == "add":
        service_id_raw = data.get("service")
        link = data.get("link")
        quantity_raw = data.get("quantity")
        runs_raw = data.get("runs", 1)
        interval_raw = data.get("interval", 0)
        comments = data.get("comments")

        if not service_id_raw or not link or not quantity_raw:
            return {"error": "Parameters 'service', 'link', and 'quantity' are required"}

        try:
            service_id = int(service_id_raw)
            quantity = int(quantity_raw)
            runs = int(runs_raw)
            interval = int(interval_raw)
        except ValueError:
            return {"error": "Invalid numeric format in parameters"}

        service = await db.get(Service, service_id)
        if not service:
            return {"error": "Service not found"}

        if quantity < service.min_quantity or quantity > service.max_quantity:
            return {"error": f"Quantity must be between {service.min_quantity} and {service.max_quantity}"}

        order_id = str(uuid.uuid4())
        is_drip = runs > 1 or interval > 0

        order = Order(
            id=order_id,
            service_id=service_id,
            target_url=link,
            quantity=quantity,
            delivered_count=0,
            remains_count=quantity,
            status="Pending",
            comments=comments,
            drip_feed=is_drip,
            interval_seconds=interval if interval > 0 else service.default_interval_seconds,
            runs=runs
        )

        db.add(order)
        await db.commit()

        # Run background simulation
        background_tasks.add_task(process_order_simulation, order_id)

        return {"order": order_id}

    # 4. ACTION: status
    elif action == "status":
        order_id = data.get("order")
        orders_str = data.get("orders")

        if orders_str:
            # Multi-order status query
            ids = [o.strip() for o in orders_str.split(",") if o.strip()]
            result = await db.execute(select(Order).where(Order.id.in_(ids)))
            orders_list = result.scalars().all()
            response_dict = {}
            for o in orders_list:
                response_dict[o.id] = {
                    "charge": "0.00",
                    "start_count": "0",
                    "status": o.status,
                    "remains": str(o.remains_count),
                    "currency": settings.MOCK_CURRENCY
                }
            return response_dict

        if not order_id:
            return {"error": "Parameter 'order' is required"}

        order = await db.get(Order, order_id)
        if not order:
            return {"error": "Incorrect order ID"}

        return {
            "charge": "0.00",
            "start_count": "0",
            "status": order.status,
            "remains": str(order.remains_count),
            "currency": settings.MOCK_CURRENCY
        }

    return {"error": f"Unknown action: {action}"}
