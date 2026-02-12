from . import database

async def get_db():
    async with database.AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()