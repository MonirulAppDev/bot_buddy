import asyncio
import ssl
import certifi
import pymysql
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# TiDB Credentials
USER = "ZogUjEbd9DhTnaX.root"
PASSWORD = "MvOffWrOrG9qn3n3"
HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
PORT = 4000
DATABASE = "botbuddy_db"


def test_sync_pymysql():
    print("Testing sync pymysql connection first...")
    try:
        conn = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE, # try botbuddy_db
            ssl={"ca": certifi.where()},
            connect_timeout=15
        )
        print("Connected to TiDB successfully via pymysql!")
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print("TiDB Version:", version)

            # Ensure botbuddy_db exists
            cursor.execute("CREATE DATABASE IF NOT EXISTS botbuddy_db")
            print("Database 'botbuddy_db' ensured/created successfully!")
        conn.close()
        return True
    except Exception as e:
        print("Sync pymysql error:", e)
        return False


async def test_async_aiomysql():
    print("\nTesting async aiomysql + SQLAlchemy connection...")
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED

    db_url = f"mysql+aiomysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    engine = create_async_engine(
        db_url,
        connect_args={"ssl": ssl_ctx},
        echo=False
    )

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            print("SQLAlchemy Async Engine Connected! Query result:", row)
        await engine.dispose()
        print("TiDB Async Verification Complete! 🚀")
        return True
    except Exception as e:
        print("Async aiomysql error:", e)
        return False


if __name__ == "__main__":
    if test_sync_pymysql():
        asyncio.run(test_async_aiomysql())
