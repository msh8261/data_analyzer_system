import os
import sys
from backend.log import logger

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)
# Get the directory path of the current file
current_dir_path = os.path.dirname(current_file_path)
# Get the parent directory path
parent_dir_path = os.path.dirname(current_dir_path)
# Add the parent directory path to the sys.path
sys.path.insert(0, parent_dir_path)
from celery import Celery
import time
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Secret key and hashing algorithm
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))

celery_app = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",  # Redis message broker
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0"  # Redis result backend
)

@celery_app.task
def long_running_task(x, y):
    time.sleep(5)  # Simulate long task
    return x + y
