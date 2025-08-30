import json
import asyncio
from aiokafka import AIOKafkaConsumer

# (EN) We need a type hint for ConnectionManager without a circular import.
# (ES) Necesitamos una pista de tipo para ConnectionManager sin una importación circular.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..main import ConnectionManager

class KafkaConsumer:
    """
    (EN) A class to manage the Kafka consumer and bridge messages to WebSockets.
    (ES) Una clase para gestionar el consumidor de Kafka y hacer de puente con los WebSockets.
    """
    def __init__(self, manager: "ConnectionManager"):
        # (EN) We "inject" the ConnectionManager to be able to send messages back to clients.
        # (ES) "Inyectamos" el ConnectionManager para poder enviar mensajes de vuelta a los clientes.
        self.manager = manager
        self.consumer = None

    async def start(self, topic: str):
        """(EN) Starts the consumer and the listening loop. / (ES) Inicia el consumidor y el bucle de escucha."""
        loop = asyncio.get_running_loop()
        self.consumer = AIOKafkaConsumer(
            topic,
            loop=loop,
            bootstrap_servers='localhost:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id="micro-manager-group"
        )
        await self.consumer.start()
        print(f"INFO:     Kafka Consumer started, listening on '{topic}'.")
        try:
            # (EN) The main loop to listen for messages.
            # (ES) El bucle principal para escuchar mensajes.
            async for msg in self.consumer:
                print(f"DEBUG:    Message received from Kafka: {msg.value}")
                message_data = msg.value
                task_id = message_data.get("taskId")
                payload = message_data.get("payload")
                
                if task_id and payload:
                    await self.manager.send_update_for_task(task_id, payload)
        finally:
            await self.stop()

    async def stop(self):
        """(EN) Stops the consumer. / (ES) Detiene al consumidor."""
        if self.consumer:
            await self.consumer.stop()
            print("INFO:     Kafka Consumer stopped.")