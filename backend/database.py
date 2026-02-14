from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declarative_base
from config import settings
# 1. Твой URL без лишних параметров
URL = settings.DATABASE_URL

# 2. Создаем асинхронный движок
engine = create_async_engine(URL,
                             pool_pre_ping=True
                             )

# 3. Переименовал в AsyncSessionLocal, чтобы main.py его увидел
# Используем async_sessionmaker — это стандарт для асинхронности
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 4. Базовый класс для моделей
class Base(DeclarativeBase): pass