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
import redis
import json
from backend.encryption import encrypt, decrypt
from backend.log import logger
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Secret key and hashing algorithm
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def set_cache(key: str, value: dict, expiration: int = 3600) -> None:
    """Store encrypted data in Redis cache.
    
    Args:
        key (str): The key under which the data is stored.
        value (dict): The data to be stored.
        expiration (int, optional): Expiration time in seconds. Defaults to 3600.
    """
    try:
        encrypted_value = encrypt(json.dumps(value))
        redis_client.set(key, encrypted_value, ex=expiration)
        logger.info(f"Cache set for key: {key}")
    except Exception as e:
        logger.error(f"Error setting cache: {e}")

def get_cache(key: str) -> dict:
    """Retrieve decrypted data from Redis cache.
    
    Args:
        key (str): The key under which the data is stored.
    
    Returns:
        dict: The decrypted data if found, otherwise None.
    """
    try:
        data = redis_client.get(key)
        if data:
            decrypted_data = json.loads(decrypt(data))
            logger.info(f"Cache hit for key: {key}")
            return decrypted_data
        logger.info(f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Error getting cache: {e}")
        return None

