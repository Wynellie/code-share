from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#datavase - создает движок и sessionmaker, для того, чтоб подключатся через него в main
# Используем 127.0.0.1 и явно задаем кодировку клиента
URL = "postgresql://user:password@127.0.0.1:5433/editor_db?client_encoding=utf8"

engine = create_engine(URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Базовый класс — от него будем наследовать все наши таблицы
Base = declarative_base()