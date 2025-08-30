# (EN) Import necessary components.
# (ES) Importamos los componentes necesarios.
import os
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from typing import List
from pydantic import ValidationError

# (EN) Import our Pydantic models from the models.py file.
# (ES) Importamos nuestros modelos Pydantic del archivo models.py.
from .models import CommandRequest, CommandResponse, CommandType

# --- 1. Connection Manager ---
# --- 1. Gestor de Conexiones ---
class ConnectionManager:
    """
    (EN) A class to manage active WebSocket connections.
    (ES) Una clase para gestionar las conexiones WebSocket activas.
    """
    def __init__(self):
        # (EN) List to store active connections.
        # (ES) Lista para almacenar las conexiones activas.
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """(EN) Accepts and stores a new connection. / (ES) Acepta y almacena una nueva conexión."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"INFO:     New connection accepted. Total clients: {len(self.active_connections)}")


    def disconnect(self, websocket: WebSocket):
        """(EN) Removes a connection from the list. / (ES) Elimina una conexión de la lista."""
        self.active_connections.remove(websocket)
        print(f"INFO:     Client disconnected. Total clients: {len(self.active_connections)}")


    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """(EN) Sends a JSON message to a specific client. / (ES) Envía un mensaje JSON a un cliente específico."""
        await websocket.send_json(message)

# (EN) Create a single instance of the manager to be used by the application.
# (ES) Creamos una única instancia del gestor para ser usada por la aplicación.
manager = ConnectionManager()

# --- 2. FastAPI Application Setup ---
# --- 2. Configuración de la Aplicación FastAPI ---
app = FastAPI(
    title="AppDroid Micro-Manager",
    description="A service to orchestrate and execute remote tasks.",
    version="0.1.0",
)

# (EN) The logic to serve the index.html and static files remains the same.
# (ES) La lógica para servir el index.html y los archivos estáticos sigue igual.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

@app.get("/")
async def get_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="index.html not found")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- 3. WebSocket Endpoint ---
# --- 3. Endpoint WebSocket ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    (EN) The main WebSocket endpoint for real-time communication.
    (ES) El endpoint WebSocket principal para la comunicación en tiempo real.
    """
    await manager.connect(websocket)
    try:
        # (EN) Loop indefinitely to listen for incoming messages.
        # (ES) Bucle infinito para escuchar los mensajes entrantes.
        while True:
            data = await websocket.receive_json()

            # (EN) We use a try/except block to validate the incoming data with Pydantic.
            # (ES) Usamos un bloque try/except para validar los datos entrantes con Pydantic.
            try:
                # (EN) Pydantic parses and validates the data. If it fails, it raises a ValidationError.
                # (ES) Pydantic parsea y valida los datos. Si falla, lanza una ValidationError.
                command_request = CommandRequest.parse_obj(data)
                
                print(f"INFO:     Command received: {command_request.command.value}")

                # --- PLACEHOLDER ---
                # (EN) For now, we just echo a success response back to the client.
                #      In the next step, we will replace this with the Kafka producer logic.
                # (ES) Por ahora, solo devolvemos una respuesta de éxito al cliente.
                #      En el siguiente paso, reemplazaremos esto con la lógica del productor de Kafka.
                response = CommandResponse(status="success", payload={"received_command": command_request.command.value})
                await manager.send_personal_message(response.dict(), websocket)

            except ValidationError as e:
                # (EN) If the data is invalid, send a detailed error message back to the client.
                # (ES) Si los datos no son válidos, enviamos un mensaje de error detallado al cliente.
                print(f"ERROR:    Invalid command received: {e.errors()}")
                response = CommandResponse(status="error", error_message="Invalid data structure.")
                await manager.send_personal_message(response.dict(), websocket)

    except WebSocketDisconnect:
        # (EN) If the client disconnects, we remove them from the manager.
        # (ES) Si el cliente se desconecta, lo eliminamos del gestor.
        manager.disconnect(websocket)