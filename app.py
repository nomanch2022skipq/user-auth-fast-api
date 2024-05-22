from fastapi import FastAPI, Depends, APIRouter, BackgroundTasks
from models import User
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
import datetime
from jose import jwt
from fastapi import Depends, HTTPException
import pytz
from db import SessionLocal
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from fastapi import HTTPException
from bson import ObjectId
from fastapi import Query
import post
import user
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware



async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
mongodb_router = APIRouter()
postgresql_router = APIRouter()


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ---------------------------------
# :: Middlewares
# ---------------------------------

# ---------------------------------
# :: CORSMiddleware
# ---------------------------------

origins = [
    "http://localhost:8001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------
# :: TrustedHostMiddleware
# ---------------------------------

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["127.0.0.1"]
)


# ---------------------------------
# :: HTTPSRedirectMiddleware
# ---------------------------------

# app.add_middleware(HTTPSRedirectMiddleware) # Redirects HTTP to HTTPS



# ---------------------------------
# :: PostgreSQL User Login
# ---------------------------------

@postgresql_router.post("/user/login")
async def check_user_login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(detail="User Not Found", status_code=404)
    user_check = bcrypt.verify(password, user.hashed_password)
    if user_check:
        pakistan_tz = pytz.timezone("Asia/Karachi")
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
            "current_time": datetime.datetime.now(pakistan_tz).strftime(
                "%d-%B-%Y %H:%M:%S"
            ),
            "expires_time": (
                datetime.datetime.now(pakistan_tz)
                + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            ).strftime("%d-%B-%Y %H:%M:%S"),
        }

    else:
        raise HTTPException(detail="Wrong credentials", status_code=404)


# ---------------------------------
# :: PostgreSQL User Registration
# ---------------------------------


@postgresql_router.post("/user/register")
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


app.include_router(
    postgresql_router, prefix="/api/auth", tags=["User Authentication with PostgreSQL"]
)


# --------------------------------- MongoDB ---------------------------------

# ---------------------------------
# :: MongoDB Operations
# ---------------------------------


client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["Fast_api_db"]
user_collection = db["user_crud"]
post_collection = db["post_crud"]


# ---------------------------------
# :: MongoDB Pydantic Models
# ---------------------------------

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    created_at: datetime.datetime = datetime.datetime.now()


class PostCreate(BaseModel):
    title: str
    content: str
    user_id: str
    created_at: datetime.datetime = datetime.datetime.now()
    

# ---------------------------------
# :: MongoDB Connection Test
# ---------------------------------


@mongodb_router.get("/test_connection")
async def test_connection():
    collections = await db.list_collection_names()
    return collections
    

# ---------------------------------
# :: MongoDB Create Collection
# ---------------------------------


@mongodb_router.post("/create_collection")
async def create_collection(CollectionName: str = None):
    try:
        if CollectionName is None:
            raise HTTPException(detail="Collection Name is required", status_code=400)
        collection = await db.create_collection(CollectionName)
        raise HTTPException(
            detail=f"Collection Created with name {CollectionName}", status_code=200
        )
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=500)
    

# ---------------------------------
# :: MongoDB Drop Collection
# ---------------------------------


@mongodb_router.post("/drop_collection")
async def drop_collection(CollectionName: str = None):
    try:
        if CollectionName is None:
            raise HTTPException(detail="Collection Name is required", status_code=400)
        if CollectionName not in await db.list_collection_names():
            raise HTTPException(
                detail=f"Collection {CollectionName} does not exist", status_code=404
            )
        collection = await db.drop_collection(CollectionName)
        raise HTTPException(
            detail=f"Collection Dropped with name {CollectionName}", status_code=200
        )
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=500)

    
# ---------------------------------
# :: MongoDB User Create
# ---------------------------------


@mongodb_router.post("/user/create", response_model=UserCreate)
async def create_user(name: str, email: str):
    try:
        user = UserCreate(name=name, email=email)
        create = await user_collection.insert_one(user.dict())
        return user
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=400)

# ---------------------------------
# :: MongoDB User Get
# ---------------------------------

@mongodb_router.get("/user/get")
async def get_user(name: str = "Noman"):
    try:
        user = await user_collection.find_one({"name": name})
        print(user)
        if user:
            new_user = user.copy()
            new_user["_id"] = str(user["_id"])
            print(new_user["_id"])
            return new_user
        else:
            raise HTTPException(detail="User not found", status_code=404)
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=500)


# ---------------------------------
# :: MongoDB User Get All
# ---------------------------------


@mongodb_router.get("/user/get_all")
async def get_all_user(
    param: str = Query(enum=["_id", "name", "email"]),
    value: str = Query(default=""),
):
    try:
        users = []
        if param == "_id":
            get_data = {param: ObjectId(value)}
        else:
            get_data = {param: value}
        async for user in user_collection.find(get_data):
            user["_id"] = str(user["_id"])
            users.append(user)
        return users
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=500)
    
    
# --------------------------------- Routes ---------------------------------

app.include_router(user.app, prefix="/api/user", tags=["User"])
app.include_router(post.app, prefix="/api/post", tags=["Post"])
app.include_router(mongodb_router, prefix='/api', tags=["Mongo DB Operations"])
