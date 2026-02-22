from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend import models, schemas
from backend.dependencies import get_db, get_current_user

router = APIRouter(
    prefix='/api/projects'
)

@router.put('/{project_id}', response_model=schemas.Project)
async def project_put(project_id: int, project_update: schemas.ProjectCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    find_project_stmt = (select(models.Project)
                         .join(models.UserProject)
                         .where(models.UserProject.project_id == project_id,
                                models.UserProject.user_id == current_user.id))
    project = await db.scalar(find_project_stmt)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.title = project_update.title
    project.content = project_update.content

    await db.commit()
    await db.refresh(project)
    return project


@router.get('/{project_id}', response_model=schemas.Project)
async def project_get(project_id: int, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    find_project_stmt = (select(models.Project)
                       .join(models.UserProject)
                       .where(models.UserProject.project_id == project_id,
                              models.UserProject.user_id == current_user.id))
    project = await db.scalar(find_project_stmt)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get('', response_model=list[schemas.Project])
async def project_getAll(current_user: models.User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    stmt = (select(models.Project)
            .join(models.UserProject)
            .where(current_user.id == models.UserProject.user_id)
            .order_by(models.Project.id.desc()))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=schemas.Project)
async def project_create(project: schemas.ProjectCreate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_project = models.Project(title=project.title, content=project.content)

    db.add(new_project)
    await db.flush()

    db.add(models.UserProject(
        user_id=current_user.id,
        project_id=new_project.id,
    ))
    await db.commit()
    await db.refresh(new_project)

    return new_project