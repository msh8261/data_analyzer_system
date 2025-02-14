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


from fastapi import HTTPException  # Add this import in database.py
from fastapi import Depends
from sqlalchemy.orm import Session
import pymongo
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from jose import JWTError, jwt
from sqlalchemy.sql import text  # Add this import
from dotenv import load_dotenv
from backend.log import logger

# Load environment variables from .env file
load_dotenv()

mysql_host = os.getenv("mysql_host", "localhost")
mysql_port = int(os.getenv("mysql_port", "3306"))
mysql_user = os.getenv("mysql_user", "root")
mysql_password = os.getenv("mysql_password", "")
mysql_database = os.getenv("mysql_database", "chatbot")

mongo_host = os.getenv("mongo_host", "localhost")  # Default to localhost
mongo_port = os.getenv("mongo_port", "27017")  # Default MongoDB port
mongo_database = os.getenv("mongo_database", "chatbot_db")  # Default


# database URL
DATABASE_URL = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"


# SQLAlchemy setup
Base = declarative_base()

# Create a MySQL engine
engine = create_engine(DATABASE_URL)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_mongo_db():
    """
    Get a MongoDB database connection.
    """
    client = pymongo.MongoClient(f"mongodb://{mongo_host}:{mongo_port}")
    db = client[mongo_database]
    logger.info("MongoDB connection established")
    try:
        yield db
    finally:
        client.close()



def init_db():
    """
    initialize the database, responsible for creating the User table
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Get a SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_db_connection(db: Session):
    try:
        db.execute(text("SELECT 1"))  # Explicitly use text()
        logger.info("Database connection is healthy.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection issue")


def get_user_from_db(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
