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

# Создаем таблицы
models.Base.metadata.create_all(bind=database.engine)
class ConnectionManager():

    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    def add(self,project_id: int, websocket: WebSocket):
        if not self.connections.get(project_id):
            self.connections[project_id] = []
        self.connections[project_id].append(websocket)

    def remove(self,project_id: int, websocket: WebSocket):
        self.connections[project_id].remove(websocket)

    async def broadcast(self, websocket: WebSocket, project_id: int, data: str):
        for connection in self.connections[project_id]:
            if connection != websocket:
                await connection.send_text(data)

manager = ConnectionManager()
update_times = {}

@app.websocket('/ws/{project_id}')
async def partial_ws_editing(project_id: int, websocket: WebSocket):
    db = database.SessionLocal()

    await websocket.accept()

    try:
        while True:
            json = await websocket.receive_json()

            print(json)
    except WebSocketDisconnect:
        pass

# @app.websocket('/ws/{project_id}')
# async def websocket_endpoint(project_id: int, websocket: WebSocket):
#
#     db = database.SessionLocal()
#
#     await websocket.accept()
#     manager.add(project_id, websocket)
#
#     data = None
#
#     try:
#         while True:
#             # возможно перейти на receive_json
#             data = await websocket.receive_text()
#
#             await manager.broadcast(websocket, project_id, data)
#
#             cur_time = time.time()
#             last_save_time = update_times.get(project_id)
#
#             if last_save_time == None or cur_time - last_save_time > 2:
#                 project = db.get(models.Project, project_id)
#                 if project:
#                     project.content = data
#                     db.commit()
#                     update_times[project_id] = cur_time
#     except WebSocketDisconnect:
#         project = db.get(models.Project, project_id)
#         project.content = data;
#         manager.remove(project_id, websocket)
#     finally:
#         db.close()

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