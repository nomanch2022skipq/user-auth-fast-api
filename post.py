from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from bson import ObjectId
from fastapi import Query
import datetime
from mongo_client import user_collection, post_collection
from algorithm import SECRET_KEY, ALGORITHM
from jose import jwt
from passlib.hash import bcrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pytz


app = APIRouter()
security = HTTPBearer()


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


@app.post("/create", response_model=PostCreate)
async def create_post(
    title: str, content: str, token: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        token = token.credentials
        user_id = str(jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["id"])
        if not await user_collection.find_one({"_id": ObjectId(user_id)}):
            raise HTTPException(detail="User not found", status_code=404)
        post = PostCreate(title=title, content=content, user_id=user_id)
        post.user_id = ObjectId(post.user_id)
        create = await post_collection.insert_one(post.dict())
        raise HTTPException(detail="Post Created", status_code=200)
    except Exception as e:
        print(e)
        raise HTTPException(detail=str(e), status_code=400)


@app.get("/get_all_posts_by_specific_user")
async def get_all_post(token: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = token.credentials
        user_id = str(jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["id"])
        posts = []
        async for post in post_collection.find({"user_id": ObjectId(user_id)}):
            post["_id"] = str(post["_id"])
            post["user_id"] = str(post["user_id"])
            posts.append(post)
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
