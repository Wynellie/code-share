from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend import models, schemas
from backend.dependencies import get_db

router = APIRouter(
    prefix='/api/projects'
)


@router.put('/{project_id}', response_model=schemas.Project)
async def project_put(project_id: int, project_update: schemas.ProjectCreate, db: AsyncSession = Depends(get_db)):
    # ИСПРАВЛЕНО: добавлен await
    project = await db.get(models.Project, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.title = project_update.title
    project.content = project_update.content

    # ИСПРАВЛЕНО: добавлены await
    await db.commit()
    await db.refresh(project)
    return project


@router.get('/{project_id}', response_model=schemas.Project)
async def project_get(project_id: int, db: AsyncSession = Depends(get_db)):
    # ИСПРАВЛЕНО: добавлен await
    project = await db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get('', response_model=list[schemas.Project])
async def project_getAll(db: AsyncSession = Depends(get_db)):
    stmt = select(models.Project).order_by(models.Project.id.desc())
    # ИСПРАВЛЕНО: Сначала await выполнения, потом scalars
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=schemas.Project)
async def project_create(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_db)):
    new_project = models.Project(title=project.title, content=project.content)

    db.add(new_project)  # add остается синхронным

    # ИСПРАВЛЕНО: добавлены await
    await db.commit()
    await db.refresh(new_project)

    return new_project