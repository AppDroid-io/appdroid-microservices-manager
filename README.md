# AppDroid Micro-Manager (Python Edition)

Un servicio para orquestar y ejecutar tareas de forma remota, construido con FastAPI.

## Cómo Empezar

1.  Asegúrate de tener Poetry instalado.
2.  Instala las dependencias:
    ```bash
    poetry install
    ```
3.  Activa el entorno virtual:
    ```bash
    poetry shell
    ```
4.  Ejecuta el servidor web y el worker en terminales separadas:
    ```bash
    # Terminal 1
    uvicorn app.main:app --reload

    # Terminal 2
    python worker.py
    ```