from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from backend import security
from backend import models, schemas
from backend.dependencies import get_db

router = APIRouter(
    prefix='/api/auth'
)

@router.post('/register',status_code=201)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(models.User).where(models.User.login == user.login)
    result = await db.execute(stmt)
    is_taken = result.scalar_one_or_none()

    if is_taken:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = models.User(
        login = user.login,
        hashed_password = security.get_password_hash(user.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {'message':'User successfully created'}


@router.post("/login")
async def login(response: Response, user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(models.User).where(models.User.login == user.login)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()  #данные из БД

    if not db_user or not security.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect login or password")

    access_token = security.create_access_token(data={"sub": str(db_user.id)})
    csrf_token = str(uuid.uuid4())

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,  # ЗАПРЕЩАЕТ доступ из JS
        samesite="lax",  # Защита от базового CSRF
        secure=False,  # True для HTTPS (в продакшене обязательно True)
        max_age=3600  # Время жизни (сек)
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # JS МОЖЕТ читать эту куку
        samesite="lax",
        secure=False,
        max_age=3600
    )
    return {"message": "Logged in successfully", "user": {"id": db_user.id, "login": db_user.login}}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    return {"message": "Logged out"}