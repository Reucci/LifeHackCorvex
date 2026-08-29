import hashlib
import hmac
import secrets
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base
import models

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)
if "password_hash" not in {column["name"] for column in inspect(engine).get_columns("users")}:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))


PASSWORD_ITERATIONS = 600_000
SESSION_LIFETIME = timedelta(days=7)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    gold: int
    daily_streak: int
    ecoling_state: str
    last_completed_date: date | None
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PASSWORD_ITERATIONS
    )
    return f"{PASSWORD_ITERATIONS}${salt.hex()}${password_hash.hex()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        iterations_text, salt_hex, expected_hex = stored_hash.split("$")
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations_text)
        )
        return hmac.compare_digest(actual.hex(), expected_hex)
    except (ValueError, TypeError):
        return False


def create_session(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    db.add(models.Session(
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        user_id=user_id,
        expires_at=datetime.utcnow() + SESSION_LIFETIME,
    ))
    db.commit()
    return token


def get_session(authorization: str | None, db: Session) -> models.Session:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in first")

    token = authorization.removeprefix("Bearer ").strip()
    session = db.query(models.Session).filter(
        models.Session.token_hash == hashlib.sha256(token.encode()).hexdigest()
    ).first()
    if session is None or session.expires_at <= datetime.utcnow():
        if session is not None:
            db.delete(session)
            db.commit()
        raise HTTPException(status_code=401, detail="Session expired. Please log in again")
    return session


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    session = get_session(authorization, db)
    user = db.query(models.User).filter(models.User.id == session.user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return user


@app.get("/")
def home():
    return {"message": "Sprout backend is working!"}


@app.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(credentials: Credentials, db: Session = Depends(get_db)):
    user = models.User(
        username=credentials.username.strip(),
        password_hash=hash_password(credentials.password),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username is already taken")
    return {"token": create_session(db, user.id), "user": user}


@app.post("/auth/login", response_model=AuthResponse)
def login(credentials: Credentials, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == credentials.username.strip()
    ).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": create_session(db, user.id), "user": user}


@app.post("/auth/logout", status_code=204)
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    session = get_session(authorization, db)
    db.delete(session)
    db.commit()


@app.get("/users/me", response_model=UserResponse)
def get_me(user: models.User = Depends(get_current_user)):
    return user


@app.post("/actions/complete")
def complete_action(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    if user.last_completed_date == today:
        return {
            "message": "Today's action was already completed",
            "gold_earned": 0,
            "user": UserResponse.model_validate(user),
        }

    yesterday = today - timedelta(days=1)
    user.daily_streak = (
        user.daily_streak + 1 if user.last_completed_date == yesterday else 1
    )
    gold_earned = 10
    user.gold += gold_earned
    user.ecoling_state = "thriving"
    user.last_completed_date = today
    db.commit()
    db.refresh(user)

    return {
        "message": "Action completed!",
        "gold_earned": gold_earned,
        "user": UserResponse.model_validate(user),
    }
