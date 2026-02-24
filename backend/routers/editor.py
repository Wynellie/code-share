import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user, get_db, get_current_user_ws
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from backend import models, schemas, database
from backend.socket_manager import manager


router = APIRouter(
    prefix='/ws'
)

updates = {}
INTERVAL = 2.0

@router.websocket('/{project_id}')
async def partial_ws_editing(project_id: int,
    websocket: WebSocket,
    # Используем get_current_user_ws
    current_user: models.User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db)
                             ):
    find_project_stmt = select(models.UserProject).where(models.UserProject.user_id == current_user.id, models.UserProject.project_id == project_id)
    user_project = await db.scalar(find_project_stmt)
    if not user_project:
        await websocket.close(code=1008)
        return
    try:

        await websocket.accept()
        await manager.add(project_id, websocket)

        while True:
            try:
                raw_data = await websocket.receive_json()
                data = schemas.ChangesEnvelope.model_validate(raw_data)
            except WebSocketDisconnect:
                # Если клиент отключился, прокидываем исключение выше, чтобы выйти из цикла
                raise
            except Exception as e:
                print("Ошибка валидации или дисконнект: ", e)
                continue

            project = await db.get(models.Project, project_id)

            if not project:
                continue

            current_text = project.content
            for change in data.changes:
                offset = change.rangeOffset
                length = change.rangeLength
                new_text = change.text
                current_text = current_text[:offset] + new_text + current_text[offset + length:]

            project.content = current_text

            update_time = updates.get(project_id)
            cur_time = time.time()
            if not update_time or cur_time - update_time > INTERVAL:
                await db.commit()
                updates[project_id] = cur_time

            await manager.broadcast(websocket, project_id, raw_data)

    except WebSocketDisconnect:
        manager.remove(project_id, websocket)