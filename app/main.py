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
from .services.mdns import mDNSRegistrar # <-- 1. Importar el nuevo servicio

# --- Application Lifecycle ---
app = FastAPI(title="AppDroid Micro-Manager")

# --- Instancias de nuestros servicios ---
kafka_consumer = KafkaConsumer(manager=manager)
mdns_registrar = mDNSRegistrar(port=8000) # <-- 2. Crear una instancia
kafka_consumer_task = None

@app.on_event("startup")
async def startup_event():
    await get_kafka_producer()
    
    # Iniciar consumidor de Kafka
    global kafka_consumer_task
    kafka_consumer_task = asyncio.create_task(kafka_consumer.start('scripting.results'))
    
    # Registrar servicio mDNS
    mdns_registrar.register() # <-- 3. Llamar al método de registro

@app.on_event("shutdown")
async def shutdown_event():
    await stop_kafka_producer()
    
    # Detener consumidor de Kafka
    if kafka_consumer_task:
        kafka_consumer_task.cancel()
    await kafka_consumer.stop()
    
    # Anular registro mDNS
    mdns_registrar.unregister() # <-- 4. Llamar al método de anulación de registro

# --- Static Files and Router ---
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# (EN) Include all the routes from our endpoints file.
# (ES) Incluimos todas las rutas de nuestro archivo de endpoints.
app.include_router(endpoints.router)