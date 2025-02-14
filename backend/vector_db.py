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
import chromadb
from backend.log import logger
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

chromadb_database = os.getenv("chromadb_database")

client = chromadb.PersistentClient()
collection = client.get_or_create_collection(chromadb_database)


def add_vector(id: str, vector: list) -> None:
    """Add a vector to the collection.

    Args:
        id (str): The ID of the vector.
        vector (list): The vector data.
    """
    collection.add(id=id, embedding=vector)


def query_vector(vector: list) -> list:
    """Query the collection for similar vectors.

    Args:
        vector (list): The vector to query.

    Returns:
        list: The top 10 similar vectors.
    """
    return collection.query(query_embeddings=[vector], n_results=10)
