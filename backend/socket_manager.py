from fastapi import WebSocket

class ConnectionManager():
    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def add(self, project_id: int, websocket: WebSocket):
        self.connections.setdefault(project_id, []).append(websocket)

    def remove(self, project_id: int, websocket: WebSocket):
        if project_id in self.connections:
            try:
                self.connections[project_id].remove(websocket)
                if not self.connections[project_id]:
                    del self.connections[project_id]
            except ValueError:
                pass

    async def broadcast(self, sender_ws: WebSocket, project_id: int, data: dict):
        if project_id not in self.connections:
            return

        active_connections = self.connections[project_id][:]

        for connection in active_connections:
            if connection != sender_ws:
                try:
                    await connection.send_json(data)
                except Exception:
                    self.remove(project_id, connection)

manager = ConnectionManager()