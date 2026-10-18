from collections.abc import AsyncGenerator
import ssl
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Prepare connection arguments for SQLite vs TiDB/MySQL
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}
elif "mysql" in settings.DATABASE_URL:
    # TiDB Serverless requires TLS encryption
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
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
    from app.models import fb_account, order, persona, service, task_log, user  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed Default Admin / Demo User if table empty
    from app.models.user import User
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
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
