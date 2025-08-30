# app/api/endpoints.py
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import ValidationError
from starlette.responses import FileResponse

from ..models import CommandRequest, CommandResponse, CommandType, ScriptManifest
from ..core.manager import manager
from ..kafka.producer import send_command
from ..services.status import get_environment_status
from ..services.system import execute_system_command

# (EN) The base directory for downloads. For security, no file outside this directory can be accessed.
# (ES) El directorio base para las descargas. Por seguridad, no se podrá acceder a ningún archivo fuera de él.
DOWNLOADS_BASE_DIR = Path.home()

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

# --- Downloads Route ---
@router.get("/downloads", response_class=FileResponse)
async def get_downloadable_file(file_path: str = Query(..., alias="file")):
    """
    (EN) Securely serves a file from the designated downloads directory.
    (ES) Sirve de forma segura un archivo desde el directorio de descargas designado.
    """
    try:
        # (EN) Resolve the path relative to the new, more general base directory.
        # (ES) Resolvemos la ruta relativa al nuevo y más general directorio base.
        secure_path = DOWNLOADS_BASE_DIR.joinpath(Path(file_path).name).resolve()
        
        # (EN) SECURITY CHECK: This logic remains the same and is now more flexible.
        # (ES) COMPROBACIÓN DE SEGURIDAD: Esta lógica sigue igual y ahora es más flexible.
        if DOWNLOADS_BASE_DIR.resolve() in secure_path.parents and secure_path.is_file():
            return FileResponse(secure_path)
        else:
            raise HTTPException(status_code=404, detail="File not found or access denied.")
            
    except Exception:
         raise HTTPException(status_code=404, detail="File not found.")

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