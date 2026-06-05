from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User as UserModel
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
import os

router = APIRouter(prefix="/auth", tags=["auth"])
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

class UserCreated(BaseModel):
    name: str
    email: str
    password: str


class User(BaseModel):
    email: str
    password: str

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

def generate_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post('/login')
def login(user: User, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user and verify_password(user.password, db_user.hashedPassword):
        token = generate_token({"user_id": db_user.id})
        return {
            "email": db_user.email,
            "token": token,
            "message": "logged in successfully"
        }
    return {"message": "invalid email or password"}


@router.post('/create-user')
def create_user(user: UserCreated, db: Session = Depends(get_db)):

    hashed_password = hash_password(user.password)
    new_user = UserModel(
        name=user.name,
        email=user.email,
        hashedPassword=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "message": "user created successfully"
    }