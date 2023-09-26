# app.py
from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserDTO(BaseModel):
    email: str
    password: str

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/auth/login")
async def login(user: UserDTO):
    token = {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ik5pY2sgSm9uZXMiLCJwaWN0dXJlIjoiYXNzZXRzL2ltYWdlcy9uaWNrLnBuZyIsImlhdCI6MTUxNjIzOTAyMn0.mSabPRMKLZlam9GNqAlqmK3TUPAdBwezgv88V61XPdA"}
    return token

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}
