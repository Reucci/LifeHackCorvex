from fastapi import FastAPI
from pydantic import BaseModel

from database import engine, SessionLocal, Base
import models


app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    username: str


@app.get("/")
def home():
    return {"message": "Sprout backend is working!"}


@app.post("/users")
def create_user(user: UserCreate):

    db = SessionLocal()

    new_user = models.User(
        username=user.username
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    db.close()

    return new_user