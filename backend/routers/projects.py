from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend import models, schemas
from backend.dependencies import get_db, get_current_user
from backend.models import RoleEnum

router = APIRouter(
    prefix='/api/projects'
)
@router.post('/{project_id}/share')
async def project_share(project_id: int, project_share: schemas.ProjectShare, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_access = select(models.UserProject).where(models.UserProject.user_id == current_user.id, models.UserProject.project_id == project_id)
    if not await db.scalar(check_access):
        raise HTTPException(status_code=403, detail="Current user has no access to project")

    target_user = await db.scalar(
        select(models.User).where(models.User.login == project_share.login)
    )
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user_project_exists = await db.scalar(
        select(models.UserProject).where(models.UserProject.project_id == project_id, models.UserProject.user_id == target_user.id)
    )
    if target_user_project_exists:
        raise HTTPException(status_code=400, detail="User already has access")

    db.add(models.UserProject(
        user_id=target_user.id,
        project_id=project_id,
        role=project_share.role
    ))
    await db.commit()

    return {
        "message": "User successfully added",
        "login": target_user.login,
        "role": project_share.role
    }

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
        role = RoleEnum.EDITOR
    ))
    await db.commit()
    await db.refresh(new_project)

    return new_project