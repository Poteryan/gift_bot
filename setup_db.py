import asyncio
from database.database import init_db
import logging

async def setup():
    logging.info("Начало инициализации базы данных...")
    await init_db()
    logging.info("База данных успешно инициализирована")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(setup())
