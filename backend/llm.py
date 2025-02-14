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
from fastapi import APIRouter
import groq
import asyncio
from dotenv import load_dotenv
from backend.log import logger

# Load environment variables from .env file
load_dotenv()


router = APIRouter()

model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
api_key = os.getenv("GROQ_API_KEY")


async def groq_llm(prompt, temperature=0.1, max_tokens=256):
    """
    Generate a response using the Groq API asynchronously for better performance.
    """
    try:
        client = groq.Client(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if response.choices:
            result = response.choices[0].message.content.strip()
            logger.info(f"Generated response: {result}")
            return result
    except Exception as e:
        logger.error(f"Unexpected error in Groq API call: {str(e)}")
        return None
