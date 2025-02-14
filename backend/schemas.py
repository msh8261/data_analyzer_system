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
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from backend.log import logger


class UserCreate(BaseModel):
    username: str
    email: EmailStr  # Ensure this field exists
    password: str


class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    query: str


class ChartRequest(BaseModel):
    query: str
    data: Any


class QueryCreate(BaseModel):
    query: str


class QueryResponse(BaseModel):
    id: int
    user_id: int
    query_text: str  # Keep this name consistent with your DB model
    analysis_result: Optional[str] = None  # Keep naming consistent

    class Config:
        from_attributes = True  # Ensures compatibility with ORM objects
