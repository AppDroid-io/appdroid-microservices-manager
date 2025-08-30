import asyncio
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import uvicorn

def show_error_and_exit(title: str, message: str):
    """
    (EN) Displays a native error dialog and exits the application.
    (ES) Muestra un diálogo de error nativo y cierra la aplicación.
    """
    root = tk.Tk()
    root.withdraw() 
    messagebox.showerror(title, message)
    sys.exit(1)

async def run_command(command: str, working_dir: Path) -> subprocess.CompletedProcess:
    """
    (EN) Executes a shell command asynchronously in a specific directory.
    (ES) Ejecuta un comando de shell de forma asíncrona en un directorio específico.
    """
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=working_dir # (EN) Set the working directory / (ES) Establecemos el directorio de trabajo
    )
    stdout, stderr = await process.communicate()
    
    return subprocess.CompletedProcess(
        command, process.returncode, stdout, stderr
    )

async def is_docker_running(project_root: Path) -> bool:
    """
    (EN) Checks if the Docker daemon is responsive.
    (ES) Comprueba si el demonio de Docker está respondiendo.
    """
    print("--- Verificando estado del demonio de Docker ---")
    result = await run_command("docker info", project_root)
    return result.returncode == 0

async def ensure_docker_compose_is_up(project_root: Path) -> bool:
    """
    (EN) Runs 'docker-compose up -d' to start all services.
    (ES) Ejecuta 'docker-compose up -d' para iniciar todos los servicios.
    """
    print("INFO: El demonio de Docker está activo. Asegurando que los servicios estén levantados...")
    
    # --- CORRECCIÓN ---
    # (EN) The docker-compose.yml file is directly in the project root.
    # (ES) El archivo docker-compose.yml está directamente en la raíz del proyecto.
    compose_file_path = project_root / "docker-compose.yml"
    
    # (EN) Check if compose file exists
    # (ES) Comprobamos si el archivo compose existe
    if not compose_file_path.is_file():
        show_error_and_exit(
            "Archivo no encontrado",
            f"No se pudo encontrar el archivo docker-compose.yml en la ruta:\n{compose_file_path}"
        )
        return False

    result = await run_command(f"docker-compose -f \"{compose_file_path}\" up -d --remove-orphans", project_root)
    
    if result.returncode != 0:
        error_message = f"No se pudieron iniciar los contenedores de Docker.\n\nError:\n{result.stderr.decode()}"
        show_error_and_exit("Error Crítico de Docker Compose", error_message)
        return False
    return True

async def wait_for_port(host: str, port: int, timeout: int = 30) -> bool:
    """
    (EN) Waits for a TCP port to be open.
    (ES) Espera a que un puerto TCP esté abierto.
    """
    print(f"--- Esperando a que el puerto {port} esté disponible (máx. {timeout}s) ---")
    for _ in range(timeout):
        try:
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            print(f"INFO: El puerto {port} está abierto y listo.")
            return True
        except (ConnectionRefusedError, OSError):
            await asyncio.sleep(1)
    
    error_message = f"El servicio en el puerto {port} no respondió a tiempo."
    show_error_and_exit("Error de Arranque de Servicio", error_message)
    return False

async def start_worker(project_root: Path):
    """
    (EN) Starts the Python worker as a background process.
    (ES) Inicia el worker de Python como un proceso en segundo plano.
    """
    print("--- Iniciando el Worker de Scripts ---")
    # (EN) We use sys.executable to ensure we're using the same Python interpreter.
    # (ES) Usamos sys.executable para asegurar que estamos usando el mismo intérprete de Python.
    command = [sys.executable, "-m", "app.worker_cli"]
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=project_root # (EN) Run from the project root / (ES) Ejecutar desde la raíz del proyecto
    )
    print(f"INFO: Worker iniciado con PID: {process.pid}")
    return process

async def start_uvicorn(project_root: Path):
    """
    (EN) Starts the Uvicorn server programmatically.
    (ES) Inicia el servidor Uvicorn de forma programática.
    """
    print("--- Iniciando el Servidor Web FastAPI ---")
    # (EN) Uvicorn needs to run with the project root as the working directory.
    # (ES) Uvicorn necesita ejecutarse con la raíz del proyecto como directorio de trabajo.
    sys.path.insert(0, str(project_root))
    config = uvicorn.Config("app.main:app", host="0.0.0.0", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """
    (EN) Main orchestration function.
    (ES) Función principal de orquestación.
    """
    project_root = Path(__file__).parent.resolve()

    print("--- Docker Pre-start Check ---")
    if not await is_docker_running(project_root):
        show_error_and_exit("Docker no está corriendo", "Por favor, inicia Docker Desktop y vuelve a lanzar la aplicación.")
        return

    await ensure_docker_compose_is_up(project_root)
    await wait_for_port("localhost", 9092) # Espera por Kafka

    print("--- Docker Pre-start Check Complete ---")
    
    worker_process = await start_worker(project_root)
    
    try:
        await start_uvicorn(project_root)
    finally:
        # (EN) Clean up the worker process on exit.
        # (ES) Limpiamos el proceso del worker al salir.
        if worker_process.returncode is None:
            print("--- Deteniendo el proceso del Worker ---")
            worker_process.terminate()
            await worker_process.wait()

if __name__ == "__main__":
    try:
        # (EN) Add tk dependency if not present
        # (ES) Añade la dependencia de tk si no está presente
        try:
            import tkinter
        except ImportError:
            print("WARN: tkinter not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "tk"], check=True)

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nINFO: Apagado solicitado por el usuario.")