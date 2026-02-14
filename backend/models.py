from enum import Enum as PyEnum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table, Enum, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.database import Base

# ORM модели для представления записей в python

#
# Переписать все под mapped
#
class RoleEnum(PyEnum):
    EDITOR = 'editor'
    VIEWER = 'viewer'


class UserProject(Base):
    __tablename__ = 'user_projects'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), primary_key=True)

    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.VIEWER)

    user: Mapped["User"] = relationship(back_populates='projects_link')
    project: Mapped["Project"] = relationship(back_populates='users_link')

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)  # Column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()

    users_link: Mapped[List["UserProject"]] = relationship(back_populates='project')

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True) #Column(Integer, primary_key=True, index=True)
    login:Mapped[str] = mapped_column(index=True, unique=True, nullable=False) #= Column(String, unique=True, nullable=False, index=True)
    hashed_password:Mapped[str] = mapped_column(nullable=False)#Column(String, nullable=False)
    is_active:Mapped[bool] = mapped_column(default=True)#Column(Boolean, default=True)
    is_superuser:Mapped[bool] = mapped_column(default=False)#Column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    projects_link: Mapped[List["UserProject"]] = relationship(back_populates="user")
