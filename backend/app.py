import os
import sys
import json
import re
# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)
# Get the directory path of the current file
current_dir_path = os.path.dirname(current_file_path)
# Get the parent directory path
parent_dir_path = os.path.dirname(current_dir_path)
# Add the parent directory path to the sys.path
sys.path.insert(0, parent_dir_path)
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
import uvicorn
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from backend.auth import get_current_user
from backend.database import get_db, init_db
from backend.models import User, Query
from backend.crud import store_query_result, execute_sql, login_user
from backend.auth import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, password_context, verify_token
from backend.log import logger
import asyncio
from fastapi import APIRouter
from backend.schemas import ChartRequest, UserCreate, UserResponse, QueryCreate, QueryResponse, QueryRequest
from backend.crud import create_user, get_user_queries
from passlib.hash import bcrypt
from dotenv import load_dotenv
from llm import groq_llm
from backend.config import db_info 

# Load environment variables from .env file
load_dotenv()


app = FastAPI()
router = APIRouter()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="frontend/")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, 
    background_tasks: BackgroundTasks
):
    logger.debug("Starting WebSocket connection")
    await websocket.accept()
    try:
        while True:
            logger.debug(f"Received data in websocket")
            data = await websocket.receive_text()  # Receive data
            logger.debug(f"Received data from client: {data}")  # Log the query for debugging
            # do some processing here and send the results
            result = {'data': data}
            # Send back the data in JSON format
            await websocket.send_json(result)

    except WebSocketDisconnect:
        logger.debug("Client disconnected")



@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    try:
        email = form_data.username  # OAuth2PasswordRequestForm sends 'username' for email
        password = form_data.password
        logger.debug(f"Login with email: {email} and password: {password}")
        return login_user(db, email, password)
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """Register a new user.
    
    Args:
        user (UserCreate): The user data.
        db (Session): The database session.
    
    Returns:
        UserResponse: The registered user data.
    """
    try:
        logger.debug(f"register user: {user.username}")
        return create_user(user, db)
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/queries", response_model=QueryResponse)
def submit_query(query: QueryCreate, user_id: int, db: Session = Depends(get_db)) -> QueryResponse:
    """Submit a new query.
    
    Args:
        query (QueryCreate): The query data.
        user_id (int): The user ID.
        db (Session): The database session.
    
    Returns:
        QueryResponse: The stored query result.
    """
    try:
        analysis_result = f"Analysis of query: {query.query}"
        return store_query_result(user_id, query.query, analysis_result, db)
    except Exception as e:
        logger.error(f"Query submission error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/queries/{user_id}", response_model=list[QueryResponse])
def get_queries(user_id: int, db: Session = Depends(get_db)) -> list[QueryResponse]:
    """Fetch all queries for a given user."""
    try:
        queries = db.query(Query).filter(Query.user_id == user_id).all()
        return [QueryResponse.model_validate(q) for q in queries]  # Auto-converts ORM to Pydantic
    except Exception as e:
        logger.error(f"Fetching queries error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



@app.post("/execute_query/")
async def execute_query(
    request: QueryRequest,
    user_id: int = Depends(get_current_user),  # Ensure only logged-in users can execute queries
    db: Session = Depends(get_db)
):
    try:
        rows = await execute_sql(request.query, db)
        logger.debug(f"Executing query: {rows}")

        # Store query results in DB for tracking
        store_query_result(user_id, request.query, rows, db)
        
        return {"data": rows}
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise HTTPException(status_code=400, detail=str(e))





# Function to extract questions from plain text
def extract_questions(text):
    lines = text.split("\n")
    questions = []
    for line in lines:
        line = line.strip()
        match = re.match(r"^\d+\.\s\*\*(.*?)\*\*$", line)  # Match numbered questions
        if match:
            questions.append(match.group(1))  # Extract clean question
    return questions

@app.post("/business_questions/")
async def generate_questions():
    try:
        prompt = f""" 
        You are an expert data scientist. Generate
        business questions from these tables: {db_info}
        """
        data = await groq_llm(prompt)

        # Log raw response from LLM
        logger.debug(f"Raw response from LLM: {data}")

        # If response is a string, treat it as plain text
        if isinstance(data, str):
            try:
                data = json.loads(data)  # Try parsing as JSON
            except json.JSONDecodeError:
                logger.warning("LLM response is not JSON, treating as plain text.")
                questions_list = extract_questions(data)  # Extract questions from raw text
                return {"questions": questions_list}

        # If JSON, extract questions from "questions" key
        if "questions" not in data:
            logger.error("Unexpected response format: missing 'questions' key.")
            raise HTTPException(status_code=500, detail="Unexpected response format from LLM")

        questions_list = extract_questions(data["questions"])
        logger.debug(f"Extracted questions: {questions_list}")
        return {"questions": questions_list}

    except Exception as e:
        logger.error(f"Business questions error: {e}")
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/chart_description/")
async def chart_description(
    request: ChartRequest
):
    try:
        logger.info(f"user query: {request.query}")
        logger.info(f"chart_data: {request.data}")
        prompt=f""" 
        You are expert data scientist to analysis this data: {request.data}
        by this question from user: {request.query}
        please explain as a data scientist in details.
        """
        desc = await groq_llm(prompt)
        logger.debug(f"description: {desc}")
        return {"description": desc}
    except Exception as e:
        logger.error(f"Description of chart error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.on_event("startup")
def startup():
    try:
        # Initialize the database
        init_db()
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8005,
        log_level="debug",
    )