from pydantic import BaseModel
from typing import Optional, List

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
        from_attributes = True

class SingleChange(BaseModel):
    rangeLength: int
    rangeOffset: int
    text: str

class ChangesEnvelope(BaseModel):
    changes: List[SingleChange]