import os
import sys

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)
# Get the directory path of the current file
current_dir_path = os.path.dirname(current_file_path)
# Get the parent directory path
parent_dir_path = os.path.dirname(current_dir_path)
# Add the parent directory path to the sys.path
sys.path.insert(0, parent_dir_path)
from kafka import KafkaProducer, KafkaConsumer
import json
from backend.log import logger
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")

# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def send_event(event: dict) -> None:
    """Send an event to Kafka.

    Args:
        event (dict): The event data.
    """
    try:
        producer.send(KAFKA_TOPIC, event)
        producer.flush()
        logger.info(f"Event sent: {event}")
    except Exception as e:
        logger.error(f"Error sending event: {e}")


def consume_events() -> None:
    """Consume events from Kafka."""
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        for message in consumer:
            logger.info(f"Received event: {message.value}")
    except Exception as e:
        logger.error(f"Error consuming events: {e}")
