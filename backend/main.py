import time
from typing import Annotated

from fastapi import FastAPI, Depends, Body, HTTPException, WebSocket
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect

from backend import models, schemas, database

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

models.Base.metadata.create_all(bind=database.engine)
class ConnectionManager():

    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def add(self,project_id: int, websocket: WebSocket):
        if not self.connections.get(project_id):
            self.connections[project_id] = []
        self.connections[project_id].append(websocket)

    def remove(self,project_id: int, websocket: WebSocket):
        self.connections[project_id].remove(websocket)

    async def broadcast(self, sender_ws: WebSocket, project_id: int, data: list):
        if project_id not in self.connections:
            return

        # Создаем копию списка для итерации, чтобы не было ошибок при удалении во время цикла
        active_connections = self.connections[project_id][:]

        for connection in active_connections:
            if connection != sender_ws:

                    await connection.send_json(data)


manager = ConnectionManager()
update_times = {}

@app.websocket('/ws/{project_id}')
async def partial_ws_editing(project_id: int, websocket: WebSocket):
    db = database.SessionLocal()
    await websocket.accept()
    await manager.add(project_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            project = db.get(models.Project, project_id)
            if not project:
                continue

            current_text = project.content
            changes = data.get("changes", [])  # Вытаскиваем имепнно список изменений

            for change in changes:  # Теперь change — это честный dict с rangeOffset
                offset = int(change['rangeOffset'])
                length = int(change['rangeLength'])
                new_text = change['text']

                current_text = current_text[:offset] + new_text + current_text[offset + length:]

            project.content = current_text
            db.commit()

            await manager.broadcast(websocket, project_id, changes)

    except WebSocketDisconnect:
        manager.remove(project_id, websocket)
    finally:
        db.close()

@app.put('/api/projects/{project_id}', response_model = schemas.Project)
async def project_put(project_id: int, project_update: schemas.ProjectCreate, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.title = project_update.title
    project.content = project_update.content
    db.commit()
    db.refresh(project)
    return project

@app.get('/api/projects/{project_id}', response_model = schemas.Project)
async def project_get(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get('/api/projects', response_model = list[schemas.Project])
async def project_getAll(db: Session = Depends(get_db)):
        stmt = select(models.Project).order_by(models.Project.id.desc())
        return db.execute(stmt).scalars().all()


@app.post("/api/projects")
async def project_create(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    new_project = models.Project(title = project.title, content = project.content)

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project