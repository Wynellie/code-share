from fastapi import Request, Depends, HTTPException, status, Cookie, Header
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend import database, models, security

async def get_db():
    async with database.AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

async def _verify_token_and_get_user(access_token: str | None, db: AsyncSession):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    if not access_token:
        raise credentials_exception

    try:
        token_value = access_token.replace("Bearer ", "")
        payload = jwt.decode(token_value, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    query = select(models.User).where(models.User.id == int(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

# Зависимость для HTTP (проверяет CSRF)
async def get_current_user(
        request: Request,
        access_token: str | None = Cookie(default=None),
        x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        csrf_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_db)
):
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        if not x_csrf_token or not csrf_token or x_csrf_token != csrf_token:
            raise HTTPException(status_code=403, detail="CSRF Token mismatch")

    return await _verify_token_and_get_user(access_token, db)

# Зависимость для WebSockets (без Request и CSRF)
async def get_current_user_ws(
        access_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_db)
):
    return await _verify_token_and_get_user(access_token, db)