import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend import models, schemas, database
from backend.socket_manager import manager


router = APIRouter(
    prefix='/ws'
)

updates = {}
INTERVAL = 2.0

@router.websocket('/{project_id}')
async def partial_ws_editing(project_id: int, websocket: WebSocket):
    await websocket.accept()
    await manager.add(project_id, websocket)

    async with database.AsyncSessionLocal() as db:
        try:
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