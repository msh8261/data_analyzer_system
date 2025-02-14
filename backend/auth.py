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
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from passlib.context import CryptContext
from backend.log import logger
import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Secret key and hashing algorithm
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_token(token: str) -> Optional[dict]:
    """
    Verifies the JWT token.
    
    Args:
        token (str): The JWT token to verify.
    
    Returns:
        dict: The decoded token payload if valid.
    
    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        # Decode the token with the secret key and the algorithm
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check for token expiration
        if payload["exp"] < datetime.utcnow().timestamp():
            raise HTTPException(status_code=401, detail="Token has expired")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def hash_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password (str): The plain password.
        hashed_password (str): The hashed password.
    
    Returns:
        bool: True if the password matches, False otherwise.
    """
    return password_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password.
    
    Args:
        password (str): The plain password.
    
    Returns:
        str: The hashed password.
    """
    return password_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        data (dict): The data to encode in the token.
        expires_delta (Optional[timedelta], optional): The token expiration time. Defaults to None.
    
    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current user from the token.
    
    Args:
        token (str): The JWT token.
        db (Session): The database session.
    
    Returns:
        User: The current user.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

