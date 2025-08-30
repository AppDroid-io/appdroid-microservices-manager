# (EN) Import necessary types for data modeling.
# (ES) Importamos los tipos necesarios para el modelado de datos.
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum
from .database import Base
from sqlalchemy import Column, String, DateTime
import datetime

# (EN) Defines the valid command types, similar to the Java Enum.
# (ES) Define los tipos de comando válidos, similar al Enum de Java.
class CommandType(str, Enum):
    EXECUTE_SCRIPT = "EXECUTE_SCRIPT"
    EXECUTE_SYSTEM_COMMAND = "EXECUTE_SYSTEM_COMMAND"
    GET_STATUS = "GET_STATUS"

# --- Models for EXECUTE_SCRIPT ---
# --- Modelos para EXECUTE_SCRIPT ---

class Source(BaseModel):
    """
    (EN) Describes the source of the code to be executed.
    (ES) Describe el origen del código que se va a ejecutar.
    """
    type: str  # (EN) e.g., "git" or "file" / (ES) ej: "git" o "file"
    uri: str   # (EN) e.g., a git URL or a local file path / (ES) ej: una URL de git o una ruta de archivo local

class Execution(BaseModel):
    """
    (EN) Defines how the code should be executed.
    (ES) Define cómo debe ejecutarse el código.
    """
    command: str          # (EN) e.g., "python" / (ES) ej: "python"
    script: str           # (EN) e.g., "main.py" / (ES) ej: "main.py"
    args: List[str] = []  # (EN) List of arguments for the script / (ES) Lista de argumentos para el script

class Dependencies(BaseModel):
    """
    (EN) Specifies the dependencies required by the script.
    (ES) Especifica las dependencias requeridas por el script.
    """
    packages: List[str] = []

class ScriptManifest(BaseModel):
    """
    (EN) The complete manifest for an EXECUTE_SCRIPT command.
    (ES) El manifiesto completo para un comando EXECUTE_SCRIPT.
    """
    # (EN) Pydantic can automatically handle camelCase from JSON to snake_case in Python
    # (ES) Pydantic puede manejar automáticamente el camelCase del JSON al snake_case de Python
    environment_name: str = Field(alias="environmentName")
    source: Source
    execution: Execution
    dependencies: Optional[Dependencies] = None

# --- Models for EXECUTE_SYSTEM_COMMAND ---
# --- Modelos para EXECUTE_SYSTEM_COMMAND ---

class SystemCommandParams(BaseModel):
    """
    (EN) The parameters for an EXECUTE_SYSTEM_COMMAND.
    (ES) Los parámetros para un EXECUTE_SYSTEM_COMMAND.
    """
    program: str
    args: List[str] = []

# --- General Communication Models ---
# --- Modelos de Comunicación Generales ---

class CommandRequest(BaseModel):
    """
    (EN) The generic structure for any command sent from the client.
    (ES) La estructura genérica para cualquier comando enviado desde el cliente.
    """
    command: CommandType
    params: Dict[str, Any] # (EN) We'll validate this more specifically later / (ES) Validaremos esto más específicamente después

class CommandResponse(BaseModel):
    """
    (EN) The generic structure for any response sent to the client.
    (ES) La estructura genérica para cualquier respuesta enviada al cliente.
    """
    status: str  # (EN) e.g., "success" or "error" / (ES) ej: "success" o "error"
    payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

# --- SQLAlchemy Model for the cache table ---
# --- Modelo SQLAlchemy para la tabla de caché ---
class SourceCache(Base):
    """
    (EN) SQLAlchemy model representing the cache of script sources.
    (ES) Modelo SQLAlchemy que representa el caché de los orígenes de los scripts.
    """
    __tablename__ = "source_cache"

    uri = Column(String, primary_key=True, index=True)
    local_path = Column(String, nullable=False)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)