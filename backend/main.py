import hashlib
import hmac
import secrets
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base
import models
from rules import choose_quests
from weather_service import get_forecast_areas, get_weather, WeatherUnavailableError

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
SINGAPORE_TIME = timezone(timedelta(hours=8))


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


class CompleteQuestRequest(BaseModel):
    quest_id: int
    quest_key: str


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
    return {"message": "Backend works!"}


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


@app.get("/weather/current")
async def current_weather(
    latitude: float,
    longitude: float,
    user: models.User = Depends(get_current_user),
):
    try:
        return await get_weather(latitude, longitude)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except WeatherUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error))


@app.get("/weather/areas")
async def weather_areas(user: models.User = Depends(get_current_user)):
    try:
        return {"areas": await get_forecast_areas()}
    except WeatherUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error))


def current_quest_slot():
    now = datetime.now(SINGAPORE_TIME)
    start = now.replace(hour=now.hour - now.hour % 2, minute=0, second=0, microsecond=0)
    return start, start + timedelta(hours=2)


@app.get("/quests/current")
@app.get("/quests/today", include_in_schema=False)
async def current_quest(
    latitude: float,
    longitude: float,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slot_start, slot_end = current_quest_slot()
    database_slot_start = slot_start.replace(tzinfo=None)
    existing = db.query(models.QuestSlot).filter(
        models.QuestSlot.user_id == user.id,
        models.QuestSlot.slot_start == database_slot_start,
    ).first()
    stored_location = (existing.weather_snapshot or {}).get("location", {}) if existing else {}
    same_location = (
        abs(stored_location.get("latitude", 0) - latitude) < 0.00001
        and abs(stored_location.get("longitude", 0) - longitude) < 0.00001
    )
    if existing and (existing.completed or same_location):
        return {
            "quest_id": existing.id,
            "options": existing.quest_options,
            "weather": existing.weather_snapshot,
            "completed": existing.completed,
            "selected_quest_key": existing.selected_quest_key,
            "slot_start": slot_start.isoformat(),
            "slot_end": slot_end.isoformat(),
        }

    try:
        weather = await get_weather(latitude, longitude)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except WeatherUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error))

    quest_options = choose_quests(
        weather,
        count=2,
        seed=f"{user.id}:{slot_start.isoformat()}",
        now=slot_start,
    )
    if existing:
        quest_slot = existing
        quest_slot.quest_options = quest_options
        quest_slot.weather_snapshot = weather
    else:
        quest_slot = models.QuestSlot(
            user_id=user.id,
            slot_start=database_slot_start,
            slot_end=slot_end.replace(tzinfo=None),
            quest_options=quest_options,
            weather_snapshot=weather,
        )
        db.add(quest_slot)
    db.commit()
    db.refresh(quest_slot)
    return {
        "quest_id": quest_slot.id,
        "options": quest_options,
        "weather": weather,
        "completed": False,
        "selected_quest_key": None,
        "slot_start": slot_start.isoformat(),
        "slot_end": slot_end.isoformat(),
    }


@app.post("/actions/complete")
def complete_action(
    completion: CompleteQuestRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slot_start, _ = current_quest_slot()
    quest_slot = db.query(models.QuestSlot).filter(
        models.QuestSlot.id == completion.quest_id,
        models.QuestSlot.user_id == user.id,
        models.QuestSlot.slot_start == slot_start.replace(tzinfo=None),
    ).first()
    if quest_slot is None:
        raise HTTPException(status_code=404, detail="The current quest slot was not found")

    if quest_slot.completed:
        return {
            "message": "This two-hour quest was already completed",
            "gold_earned": 0,
            "user": UserResponse.model_validate(user),
            "completed": True,
        }

    selected_quest = next(
        (quest for quest in quest_slot.quest_options if quest["id"] == completion.quest_key),
        None,
    )
    if selected_quest is None:
        raise HTTPException(status_code=400, detail="Select one of the offered quests")

    today = datetime.now(SINGAPORE_TIME).date()
    yesterday = today - timedelta(days=1)
    if user.last_completed_date != today:
        user.daily_streak = (
            user.daily_streak + 1 if user.last_completed_date == yesterday else 1
        )
    gold_earned = int(selected_quest["points"])
    user.gold += gold_earned
    user.ecoling_state = "thriving"
    user.last_completed_date = today
    quest_slot.completed = True
    quest_slot.selected_quest_key = selected_quest["id"]
    quest_slot.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {
        "message": "Action completed!",
        "gold_earned": gold_earned,
        "user": UserResponse.model_validate(user),
        "completed": True,
        "selected_quest_key": selected_quest["id"],
    }
