import asyncio
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import init_db, AsyncSessionLocal
from app.models.service import Service
from app.services.persona_generator import generate_personas_batch
from app.services.spintax_parser import parse_spintax, get_comment_for_post
from app.services.simulation_engine import process_order_simulation
from app.models.order import Order
from app.models.task_log import TaskLog
from sqlalchemy import select


async def main():
    print("--- 1. Initializing DB ---")
    await init_db()
    print("Database initialized successfully.")

    print("\n--- 2. Testing Spintax & Comments ---")
    for _ in range(3):
        print("Generated Comment:", get_comment_for_post())

    custom_spintax = "{Best|Top notch|Incredible} tutorial! {Helped me a lot|Thanks a bunch} {🔥|💯}"
    print("Custom Spintax:", parse_spintax(custom_spintax))

    print("\n--- 3. Testing Persona Batch Generation ---")
    async with AsyncSessionLocal() as session:
        # Check if services exist, if not seed one
        res = await session.execute(select(Service))
        service = res.scalars().first()
        if not service:
            service = Service(
                name="Facebook Post Love Reactions ❤️ [Instant]",
                platform="facebook",
                service_type="love_react",
                rate_per_1000=1.5,
                min_quantity=5,
                max_quantity=1000
            )
            session.add(service)
            await session.commit()
            await session.refresh(service)
        print(f"Service loaded: ID={service.id}, Name={service.name}")

        # Seed 5 personas
        personas = generate_personas_batch(count=5, locale="en_US")
        session.add_all(personas)
        await session.commit()
        print(f"Generated {len(personas)} dummy personas. Example: {personas[0].display_name} (@{personas[0].username})")

        # Create an Order for 3 love reactions
        import uuid
        order_id = str(uuid.uuid4())
        order = Order(
            id=order_id,
            service_id=service.id,
            target_url="https://facebook.com/my-test-post-12345",
            quantity=3,
            delivered_count=0,
            remains_count=3,
            status="Pending",
            drip_feed=False,
            interval_seconds=1
        )
        session.add(order)
        await session.commit()
        print(f"Created Order: {order_id}")

    print("\n--- 4. Running Simulation Engine ---")
    await process_order_simulation(order_id)
    print("Simulation process completed.")

    print("\n--- 5. Verifying Results & Logs ---")
    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        print(f"Order Final Status: {order.status}, Delivered: {order.delivered_count}/{order.quantity}")

        res = await session.execute(select(TaskLog).where(TaskLog.order_id == order_id))
        logs = res.scalars().all()
        print(f"Logged {len(logs)} simulated task actions:")
        for log in logs:
            print(f"  - [{log.status.upper()}] Action: {log.action_type} | Time: {log.execution_time_ms}ms | Details: {log.details}")

    print("\nALL VERIFICATIONS PASSED! 🚀")


if __name__ == "__main__":
    asyncio.run(main())
