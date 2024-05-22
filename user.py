from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import datetime
from mongo_client import user_collection
from algorithm import SECRET_KEY, ALGORITHM
from jose import jwt
from passlib.hash import bcrypt


# ---------------------------------
# :: APIRouter
# ---------------------------------

app = APIRouter()

# ---------------------------------
# :: Pydentics Models
# ---------------------------------
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    created_at: datetime.datetime = datetime.datetime.now()
    
    
# ---------------------------------
# :: Create User
# ---------------------------------

@app.post("/create_user")
async def create_user(
    name: str,
    email: str,
    password: str,
):
    try:
        password = bcrypt.encrypt(password)
        if await user_collection.find_one({"name": name}):
            return {"message": "User already exists"}
        create = await user_collection.insert_one(
            {
                "name": name,
                "email": email,
                "password": password,
                "created_at": datetime.datetime.now(),
            }
        )
        return {"message": "User Created", "user": name}
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=500)
    

# ---------------------------------
# :: Login User
# ---------------------------------

@app.post("/login_user")
async def login_user(username: str, password: str):
    try:
        user = await user_collection.find_one({"name": username})
        if user:
            if bcrypt.verify(password, user["password"]):
                token = jwt.encode(
                    {
                        "user": user["name"],
                        "id": str(user["_id"]),
                    },
                    SECRET_KEY,
                    algorithm=ALGORITHM,
                )
                print(token)
                return {"message": "Login Successfull", "token": token}
            else:
                raise HTTPException(detail="Wrong Credentials", status_code=404)
        else:
            raise HTTPException(detail="User not found", status_code=404)
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=500)