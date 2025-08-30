# app/api/endpoints.py
import os
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from starlette.responses import FileResponse

from ..models import CommandRequest, CommandResponse, CommandType, ScriptManifest
from ..core.manager import manager
from ..kafka.producer import send_command
from ..services.status import get_environment_status

# (EN) Create an APIRouter. This is like a mini-FastAPI app.
# (ES) Creamos un APIRouter. Es como una mini-aplicación de FastAPI.
router = APIRouter()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static")

# --- HTTP Routes ---
@router.get("/", response_class=FileResponse)
async def get_language_selector():
    return os.path.join(STATIC_DIR, "index.html")

@router.get("/es", response_class=FileResponse)
async def get_dashboard_es():
    return os.path.join(STATIC_DIR, "es.html")

@router.get("/en", response_class=FileResponse)
async def get_dashboard_en():
    return os.path.join(STATIC_DIR, "en.html")

# --- WebSocket Route ---
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            try:
                command_request = CommandRequest.parse_obj(data)
                
                if command_request.command == CommandType.GET_STATUS:
                    status_data = await get_environment_status()
                    response_payload = {"type": "ENVIRONMENT_STATUS", "data": status_data}
                    response = CommandResponse(status="success", payload=response_payload)
                    await websocket.send_json(response.dict())
                
                elif command_request.command == CommandType.EXECUTE_SCRIPT:
                    task_id = f"task-{uuid.uuid4()}"
                    await manager.associate_task_with_socket(task_id, websocket)
                    initial_response = CommandResponse(status="accepted", payload={"taskId": task_id})
                    await websocket.send_json(initial_response.dict())
                    
                    script_manifest = ScriptManifest.parse_obj(command_request.params)
                    kafka_message = {"taskId": task_id, "manifest": script_manifest.dict(by_alias=True)}
                    await send_command("web-commands", kafka_message)
                else:
                    await websocket.send_json(
                        CommandResponse(status="error", error_message="Command not implemented yet.").dict()
                    )
            except ValidationError as e:
                await websocket.send_json(
                    CommandResponse(status="error", error_message=f"Invalid data format: {e.errors()}").dict()
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)