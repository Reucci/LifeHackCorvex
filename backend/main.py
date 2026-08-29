from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date

from database import engine, SessionLocal, Base
import models

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/users/{user_id}")
def get_user(user_id: int):
    db = SessionLocal()

    user = db.query(models.User).filter(models.User.id == user_id).first()

    db.close()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@app.post("/users/{user_id}/complete")
def complete_action(user_id: int):
    db = SessionLocal()

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Example game logic
    points_earned = 10

    user.score += points_earned
    user.streak += 1
    user.sprout_state = "thriving"
    user.last_completed_date = date.today()

    db.commit()
    db.refresh(user)

    db.close()

    return {
        "message": "Action completed!",
        "points_earned": points_earned,
        "user": user
    }