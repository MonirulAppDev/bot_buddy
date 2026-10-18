from collections.abc import AsyncGenerator
import ssl
import sys
import certifi
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# On Windows, set SelectorEventLoop to ensure async TLS connection to TiDB Cloud
if sys.platform == "win32":
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# Prepare connection arguments for SQLite vs TiDB Cloud MySQL
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}
elif "mysql" in settings.DATABASE_URL:
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    connect_args = {"ssl": ctx}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
    pool_recycle=300 if "mysql" in settings.DATABASE_URL else -1,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    # Import all models so metadata registers all tables
    from app.models import fb_account, fb_page, order, persona, service, task_log, user  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed Default Admin & Demo Services if empty
    from app.models.user import User
    from app.models.service import Service
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # 1. Seed Admin
        res = await session.execute(select(User).limit(1))
        existing_user = res.scalars().first()
        if not existing_user:
            admin_user = User(
                username="admin",
                email="admin@botbuddy.local",
                hashed_password=hash_password("admin123456"),
                api_key="bb_live_master_api_key_778899",
                balance=100.00,
                role="admin"
            )
            session.add(admin_user)
            await session.commit()

        # 2. Seed Services if empty
        srv_res = await session.execute(select(Service).limit(1))
        if not srv_res.scalars().first():
            from app.api.v1.services import DEFAULT_SERVICES
            for s in DEFAULT_SERVICES:
                session.add(Service(**s))
            await session.commit()
