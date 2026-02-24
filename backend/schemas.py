from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend import models
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
class ProjectShare(BaseModel):
    login: str
    role: models.RoleEnum = models.RoleEnum.VIEWER

class SingleChange(BaseModel):
    rangeLength: int
    rangeOffset: int
    text: str

class ChangesEnvelope(BaseModel):
    changes: List[SingleChange]

class UserCreate(BaseModel):
    login: str = Field(min_length=4, max_length=32)
    password: str

class UserResponse(BaseModel):
    id: int
    login: str
    class Config:
        from_attributes = True