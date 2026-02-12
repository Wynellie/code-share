from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. Твой URL без лишних параметров
URL = "postgresql+asyncpg://user:password@127.0.0.1:5433/editor_db"

# 2. Создаем асинхронный движок
engine = create_async_engine(URL)

# 3. Переименовал в AsyncSessionLocal, чтобы main.py его увидел
# Используем async_sessionmaker — это стандарт для асинхронности
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 4. Базовый класс для моделей
Base = declarative_base()