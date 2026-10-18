import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.order import Order
from app.models.persona import Persona
from app.models.service import Service
from app.models.task_log import TaskLog
from app.services.drip_engine import get_stochastic_delay
from app.services.persona_generator import generate_personas_batch
from app.services.spintax_parser import get_comment_for_post

logger = logging.getLogger("simulation_engine")


async def ensure_available_personas(session: AsyncSession, minimum_needed: int = 20) -> list[Persona]:
    """Ensure we have enough dummy personas in the pool to simulate actions."""
    result = await session.execute(select(Persona).where(Persona.status == "active").limit(minimum_needed))
    personas = list(result.scalars().all())

    if len(personas) < minimum_needed:
        deficit = minimum_needed - len(personas)
        logger.info(f"Generating {deficit} new dummy personas...")
        new_personas = generate_personas_batch(count=deficit)
        session.add_all(new_personas)
        await session.commit()
        for p in new_personas:
            personas.append(p)

    return personas


async def process_order_simulation(order_id: str):
    """Background worker that simulates the delivery of an engagement order."""
    async with AsyncSessionLocal() as session:
        # 1. Fetch order & service
        order = await session.get(Order, order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return

        service = await session.get(Service, order.service_id)
        if not service:
            order.status = "Canceled"
            await session.commit()
            return

        order.status = "In progress"
        await session.commit()

        # 2. Prepare personas pool
        personas = await ensure_available_personas(session, minimum_needed=min(order.quantity, 50))
        persona_count = len(personas)

        # 3. Execution loop
        remaining = order.quantity - order.delivered_count
        base_interval = float(order.interval_seconds if order.drip_feed else 0.2)

        for step in range(remaining):
            start_time = asyncio.get_event_loop().time()
            
            # Select persona round-robin or randomly
            persona = personas[step % persona_count] if persona_count > 0 else None
            
            action_type = service.service_type
            details = f"Delivered 1 {action_type} to {order.target_url}"
            
            if "comment" in action_type:
                comment_text = get_comment_for_post(order.comments)
                details = f"Comment: \"{comment_text}\""

            # Apply stochastic delay
            delay = get_stochastic_delay(base_interval, min_floor=0.05 if not order.drip_feed else 1.0)
            await asyncio.sleep(delay)

            exec_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            # Log task
            task_log = TaskLog(
                id=str(uuid.uuid4()),
                order_id=order.id,
                persona_id=persona.id if persona else None,
                action_type=action_type,
                status="success",
                execution_time_ms=exec_time_ms,
                details=details
            )
            session.add(task_log)

            if persona:
                persona.total_actions += 1

            order.delivered_count += 1
            order.remains_count = max(0, order.quantity - order.delivered_count)

            # Commit periodically or at the end to keep DB responsive
            if (step + 1) % 5 == 0 or (step + 1) == remaining:
                order.updated_at = datetime.now(timezone.utc)
                await session.commit()

        # 4. Final status
        order.status = "Completed"
        order.remains_count = 0
        order.updated_at = datetime.now(timezone.utc)
        await session.commit()
        logger.info(f"Order {order_id} simulation completed successfully.")
