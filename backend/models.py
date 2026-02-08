from sqlalchemy import Column, Integer, String, Text
from backend.database import Base

# ORM модели для представления записей в python

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)