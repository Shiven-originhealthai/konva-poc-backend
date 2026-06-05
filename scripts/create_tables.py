"""One-shot script to create all tables directly (use alembic for production)."""
import asyncio
from app.db.session import engine
from app.db.base import Base
import app.models.user  # noqa: F401
import app.models.thumbnail  # noqa: F401


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


if __name__ == "__main__":
    asyncio.run(main())
