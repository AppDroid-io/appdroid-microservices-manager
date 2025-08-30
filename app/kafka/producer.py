import json
import asyncio
from aiokafka import AIOKafkaProducer
from ..models import CommandRequest

# (EN) We'll use a singleton pattern for the producer instance.
# (ES) Usaremos un patrón singleton para la instancia del productor.
_producer = None

async def get_kafka_producer():
    """
    (EN) Initializes and returns a singleton AIOKafkaProducer instance.
    (ES) Inicializa y devuelve una instancia única de AIOKafkaProducer.
    """
    global _producer
    if _producer is None:
        loop = asyncio.get_running_loop()
        _producer = AIOKafkaProducer(
            loop=loop,
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await _producer.start()
        print("INFO:     Kafka Producer started.")
    return _producer

async def stop_kafka_producer():
    """(EN) Stops the producer. / (ES) Detiene al productor."""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        print("INFO:     Kafka Producer stopped.")

async def send_command(topic: str, message: dict):
    """
    (EN) Sends a command message to the specified Kafka topic.
    (ES) Envía un mensaje de comando al topic de Kafka especificado.
    """
    producer = await get_kafka_producer()
    try:
        await producer.send_and_wait(topic, message)
        print(f"INFO:     Message sent to Kafka topic '{topic}'")
    except Exception as e:
        print(f"ERROR:    Could not send message to Kafka: {e}")