# app/services/system.py
import asyncio
import sys
from pathlib import Path
from ..models import SystemCommandParams

# (EN) A whitelist of safe, pre-approved commands.
# (ES) Una lista blanca de comandos seguros y pre-aprobados.
# We map a simple name to the actual command for different OS.
# Mapeamos un nombre simple al comando real para diferentes SO.
COMMAND_WHITELIST = {
    "open_user_folder": {
        "win32": "explorer",
        "darwin": "open",  # macOS
        "linux": "xdg-open", # Linux
    }
}

async def execute_system_command(params: SystemCommandParams):
    """
    (EN) Safely executes a whitelisted system command.
    (ES) Ejecuta de forma segura un comando de sistema de la lista blanca.
    """
    command_key = params.program
    
    if command_key not in COMMAND_WHITELIST:
        error_message = f"Command '{command_key}' is not allowed."
        print(f"ERROR:    {error_message}")
        return {"status": "error", "message": error_message}

    # (EN) Get the correct command for the current operating system.
    # (ES) Obtenemos el comando correcto para el sistema operativo actual.
    command = COMMAND_WHITELIST[command_key].get(sys.platform)

    if not command:
        error_message = f"Command '{command_key}' is not supported on this OS ({sys.platform})."
        print(f"ERROR:    {error_message}")
        return {"status": "error", "message": error_message}
    
    # (EN) Determine the target path in a cross-platform way.
    # (ES) Determinamos la ruta de destino de forma multiplataforma.
    target_path = Path.home() / "Videos"
    target_path.mkdir(exist_ok=True) # (EN) Ensure the directory exists. / (ES) Aseguramos que el directorio exista.

    full_command = f'"{command}" "{target_path}"'
    
    print(f"INFO:     Executing system command: {full_command}")

    process = await asyncio.create_subprocess_shell(full_command)
    await process.wait()

    if process.returncode == 0:
        return {"status": "success", "message": f"Command '{command_key}' executed."}
    else:
        return {"status": "error", "message": f"Command '{command_key}' failed."}