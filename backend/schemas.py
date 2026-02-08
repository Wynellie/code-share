from pydantic import BaseModel
from typing import Optional

# Создаем схемы для валидирования pydantic, для получения и отправки данных на фронт


class ProjectBase(BaseModel):
    title: str
    content: Optional[str] = ""

# Схема для СОЗДАНИЯ
class ProjectCreate(ProjectBase):
    pass  # Тут те же поля, что в Base

# Схема для ОТВЕТА
class Project(ProjectBase):
    id: int

    class Config:
        # Это мастхэв, чтобы Pydantic умел читать данные прямо из SQLAlchemy объектов
        from_attributes = True