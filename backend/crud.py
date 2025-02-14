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
import json
from decimal import Decimal  # ✅ Import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.models import User, Query
from backend.schemas import UserCreate, QueryCreate  
from backend.auth import get_password_hash, verify_password, create_access_token, password_context 
from backend.schemas import UserCreate, QueryCreate
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.main import get_sql_query
from backend.log import logger


def create_user(user: UserCreate, db: Session) -> User:
    """Create a new user.
    
    Args:
        user (UserCreate): The user data.
        db (Session): The database session.
    
    Returns:
        User: The created user.
    """
    try:
        hashed_password = get_password_hash(user.password)
        db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created: {user.username}")
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def authenticate_user(db: Session, email: EmailStr, password: str) -> User:
    """Authenticate a user.
    
    Args:
        db (Session): The database session.
        email (EmailStr): The user email.
        password (str): The password.
    
    Returns:
        User: The authenticated user.
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def login_user(db: Session, email: EmailStr, password: str) -> dict:
    """Login a user.
    
    Args:
        db (Session): The database session.
        email (EmailStr): The user email.
        password (str): The password.
    
    Returns:
        dict: The access token and token type.
    """
    try:
        user = authenticate_user(db, email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        access_token = create_access_token({"sub": str(user.id)})
        logger.info(f"User email logged in: {email}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



def store_query_result(user, query_text: str, analysis_result: dict | list, db: Session) -> Query:
    """Store a query result in the database.
    
    Args:
        user (User | int): The User object or user ID.
        query_text (str): The executed SQL query.
        analysis_result (dict | list): The analysis result (converted to JSON).
        db (Session): The database session.
    
    Returns:
        Query: The stored query object.
    """
    try:
        # ✅ Extract user ID if a User object is provided
        user_id = user.id if hasattr(user, "id") else user

        if not isinstance(user_id, int):
            raise ValueError(f"Invalid user_id: {user_id}")

        # ✅ Convert analysis_result to JSON
        analysis_result_json = json.dumps(analysis_result)

        db_query = Query(
            user_id=user_id, 
            query_text=query_text, 
            analysis_result=analysis_result_json  # ✅ Store JSON string
        )
        
        db.add(db_query)
        db.commit()
        db.refresh(db_query)
        
        logger.info(f"Query successfully stored for user {user_id}")
        return db_query

    except Exception as e:
        logger.error(f"Error storing query result: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_user_queries(user_id: int, db: Session) -> list[Query]:
    """Get all queries for a user.
    
    Args:
        user_id (int): The user ID.
        db (Session): The database session.
    
    Returns:
        list[Query]: The list of queries.
    """
    try:
        queries = db.query(Query).filter(Query.user_id == user_id).all()
        logger.info(f"Queries fetched for user {user_id}")
        return queries
    except Exception as e:
        logger.error(f"Error fetching user queries: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




async def execute_sql(query:str, db: Session):
    try:
        # Await the result of the asynchronous get_sql function
        result = await get_sql_query(query)  # Await here

        # The generated SQL is wrapped in a list, so we need to extract the query
        result_sql = str(result["sql"][0])  # Extract the first item from the list

        logger.debug(f"Executing query: {result_sql}")

        result = db.execute(text(result_sql))
        logger.debug(f"Query result: {result}")

        # Fetch all rows from the result and convert them into a list of dictionaries
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]

        # Convert Decimal to float for easier handling in JavaScript
        for row in rows:
            row["total_sales_units"] = float(row["total_sales_units"])

        logger.debug(f"Rows: {rows}")
        return rows
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

