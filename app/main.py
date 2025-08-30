# app/main.py
import asyncio
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
import os

# (EN) Import the services and router from our new atomized files.
# (ES) Importamos los servicios y el router de nuestros nuevos archivos atomizados.
from .kafka.producer import get_kafka_producer, stop_kafka_producer
from .kafka.consumer import KafkaConsumer
from .core.manager import manager
from .api import endpoints

# --- Application Lifecycle ---
app = FastAPI(title="AppDroid Micro-Manager")
kafka_consumer = KafkaConsumer(manager=manager)
kafka_consumer_task = None

@app.on_event("startup")
async def startup_event():
    await get_kafka_producer()
    global kafka_consumer_task
    kafka_consumer_task = asyncio.create_task(kafka_consumer.start('scripting.results'))

@app.on_event("shutdown")
async def shutdown_event():
    await stop_kafka_producer()
    if kafka_consumer_task:
        kafka_consumer_task.cancel()
    await kafka_consumer.stop()

# --- Static Files and Router ---
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# (EN) Include all the routes from our endpoints file.
# (ES) Incluimos todas las rutas de nuestro archivo de endpoints.
app.include_router(endpoints.router)