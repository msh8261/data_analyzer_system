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
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
from backend.log import logger

try:

    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, index=True)
        username = Column(String(255), unique=True, index=True)
        email = Column(String(255), unique=True, index=True)
        hashed_password = Column(String(255))
        queries = relationship("Query", back_populates="user")

    class Query(Base):
        __tablename__ = "queries"

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"))
        query_text = Column(Text, nullable=False)
        analysis_result = Column(Text, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

        user = relationship("User", back_populates="queries")
except Exception as e:
    logger.error(f"Error occurred while defining models: {e}")
    raise
