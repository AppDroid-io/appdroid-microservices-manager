# app/core/manager.py
from typing import Dict, List
from fastapi import WebSocket
from ..models import CommandResponse

class ConnectionManager:
    """
    (EN) Manages active WebSocket connections and task associations.
    (ES) Gestiona las conexiones WebSocket activas y las asociaciones de tareas.
    """
    def __init__(self):
        self.task_to_socket: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        print(f"INFO:     New connection accepted from: {websocket.client.host}")

    def disconnect(self, websocket: WebSocket):
        tasks_to_remove = [task_id for task_id, sock in self.task_to_socket.items() if sock == websocket]
        for task_id in tasks_to_remove:
            del self.task_to_socket[task_id]
        print(f"INFO:     Client disconnected. Removed {len(tasks_to_remove)} task associations.")

    async def associate_task_with_socket(self, task_id: str, websocket: WebSocket):
        self.task_to_socket[task_id] = websocket

    async def send_update_for_task(self, task_id: str, payload: dict):
        websocket = self.task_to_socket.get(task_id)
        if websocket:
            response = CommandResponse(status="progress", payload=payload)
            await websocket.send_json(response.dict())
            print(f"INFO:     Sent update for task {task_id} to client.")
        else:
            print(f"WARN:     Received update for unknown or disconnected task: {task_id}")

# (EN) Create a single, shared instance of the manager.
# (ES) Creamos una única instancia compartida del gestor.
manager = ConnectionManager()