import ssl
import asyncpg
from . import config
import contextlib
from typing import AsyncGenerator

pool = None

async def get_pool() -> asyncpg.Pool:
    return pool

async def init_db_pool() -> None:
    global pool
    try:
        ssl_ctx = ssl.create_default_context() if config.DATABASE_SSL else None
        pool = await asyncpg.create_pool(
            dsn=config.DATABASE_URL,
            min_size=config.DB_POOL_MIN,
            max_size=config.DB_POOL_MAX,
            ssl=ssl_ctx,
        )
        print("Database connection pool initialized successfully.")
    except Exception as e:
        print(f"Failed to create database connection pool: {e}")
        raise

async def close_db_pool() -> None:
    global pool
    if pool is not None:
        try:
            await pool.close()
            print("Database connection pool closed successfully.")
        except Exception as e:
            print(f"Error closing database connection pool: {e}")
        finally:
            pool = None

@contextlib.asynccontextmanager
async def lifespan_context(app) -> AsyncGenerator[None, None]:
    try:
        await init_db_pool()
        yield
    finally:
        await close_db_pool()