# app/worker_cli.py
import asyncio
import json
from aiokafka import AIOKafkaConsumer

# (EN) Imports are now relative because this file is inside the 'app' package.
# (ES) Las importaciones ahora son relativas porque este archivo está dentro del paquete 'app'.
from .database import AsyncSessionLocal, Base, engine
from .models import ScriptManifest, Source
from .services.workspace import WorkspaceService
from .services.execution import ScriptExecutionService

async def main():
    """
    (EN) Main function for the worker. Connects to Kafka and processes messages.
    (ES) Función principal para el worker. Se conecta a Kafka y procesa los mensajes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    workspace_service = WorkspaceService()
    execution_service = ScriptExecutionService()

    consumer = AIOKafkaConsumer(
        'web-commands',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id="script-worker-group"
    )
    await consumer.start()
    print("INFO:     Worker started, listening on 'web-commands'.")
    try:
        async for msg in consumer:
            print(f"INFO:     Job received from Kafka: {msg.value}")
            data = msg.value
            task_id = data.get("taskId")
            manifest_data = data.get("manifest")

            if task_id and manifest_data:
                manifest = ScriptManifest.parse_obj(manifest_data)
                
                async with AsyncSessionLocal() as session:
                    try:
                        workspace_path = await workspace_service.prepare_workspace(
                            session, manifest.environment_name, manifest.source
                        )
                        await execution_service.run_script(
                            manifest, workspace_path, task_id
                        )
                    except Exception as e:
                        print(f"ERROR:    [{task_id}] Critical error during task processing: {e}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())