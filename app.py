
from fastapi import FastAPI, Depends
from models import User
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
import datetime
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pytz
from db import SessionLocal




async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30    


@app.post("/user/login")
async def check_user_login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(detail="User Not Found", status_code=404)
    user_check = bcrypt.verify(password, user.hashed_password)
    if user_check:
        pakistan_tz = pytz.timezone('Asia/Karachi')
        token = jwt.encode(
            {
                "user": user.username,
                "exp": datetime.datetime.now(pakistan_tz)
                + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        print(token)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expire_in": f"{ACCESS_TOKEN_EXPIRE_MINUTES} minutes",
            'current_time': datetime.datetime.now(pakistan_tz).strftime("%d-%B-%Y %H:%M:%S"),
            "expires_time": (
                datetime.datetime.now(pakistan_tz)
                + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            ).strftime("%d-%B-%Y %H:%M:%S"),
            
        }
        
    else:
        raise HTTPException(detail="Wrong credentials", status_code=404)


@app.post("/user/register")
async def register_user(
    full_name: str,
    username: str,
    password: str,
    email: str,
    db: Session = Depends(get_db),
):
    try:
        hash_password = bcrypt.encrypt(password)
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(detail="Username already exists", status_code=400)
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password,
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=500)

