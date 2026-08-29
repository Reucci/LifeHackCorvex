import hashlib
import hmac
import os
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

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:3000,"
    "http://127.0.0.1:3000"
)
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ECOLINGS_FRONTEND_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)
if "password_hash" not in {column["name"] for column in inspect(engine).get_columns("users")}:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
if "preferences" not in {column["name"] for column in inspect(engine).get_columns("users")}:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN preferences JSON NOT NULL DEFAULT '{}'"))


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


class Preferences(BaseModel):
    display_name: str = Field(default="Eco Friend", max_length=24)
    reminders: bool = False
    reminder_time: str = Field(default="09:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    sound: bool = True
    units: str = Field(default="metric", pattern=r"^(metric|imperial)$")


BADGES = (
    ("first-step", "🌱", "First Step", "Complete your first eco action.", "actions", 1),
    ("getting-started", "🍃", "Getting Started", "Earn 100 total gold.", "gold", 100),
    ("level-two", "⭐", "Level Up", "Earn 250 total gold.", "gold", 250),
    ("week-warrior", "🔥", "Week Warrior", "Keep a 7-day streak going.", "streak", 7),
    ("hot-streak", "💥", "Hot Streak", "Reach a 14-day streak.", "streak", 14),
    ("dedicated", "📅", "Dedicated", "Complete actions on 10 different days.", "days", 10),
    ("rain-or-shine", "🌧️", "Rain or Shine", "Complete a hard weather quest.", "hard", 1),
    ("planet-protector", "🌍", "Planet Protector", "Complete 14 eco actions.", "actions", 14),
    ("eco-hero", "🏆", "Eco Hero", "Earn 1,000 total gold.", "gold", 1000),
)


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


def completed_slots(db: Session, user_id: int):
    return db.query(models.QuestSlot).filter(
        models.QuestSlot.user_id == user_id,
        models.QuestSlot.completed.is_(True),
    ).order_by(models.QuestSlot.completed_at.desc()).all()


def selected_quest(slot: models.QuestSlot):
    return next(
        (option for option in slot.quest_options if option.get("id") == slot.selected_quest_key),
        {},
    )


def longest_daily_streak(slots):
    dates = sorted({slot.completed_at.date() for slot in slots if slot.completed_at})
    longest = current = 0
    previous = None
    for completed_date in dates:
        current = current + 1 if previous and completed_date == previous + timedelta(days=1) else 1
        longest = max(longest, current)
        previous = completed_date
    return longest


@app.get("/quests/history")
def quest_history(
    limit: int = 90,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slots = completed_slots(db, user.id)[:max(1, min(limit, 365))]
    entries = []
    for slot in slots:
        quest = selected_quest(slot)
        weather = slot.weather_snapshot or {}
        observation = (weather.get("observations") or {}).get("temperature") or {}
        forecast = weather.get("forecast") or {}
        entries.append({
            "id": slot.id,
            "date": slot.completed_at.date().isoformat(),
            "completed_at": slot.completed_at.isoformat() + "Z",
            "habit": quest.get("title", "Eco action"),
            "points": int(quest.get("points", 0)),
            "difficulty": quest.get("difficulty", "easy"),
            "weather": {
                "condition": forecast.get("condition"),
                "temp": observation.get("value"),
                "area": forecast.get("area"),
            },
        })
    return {"entries": entries, "completed_dates": sorted({entry["date"] for entry in entries})}


@app.get("/users/me/stats")
def user_stats(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slots = completed_slots(db, user.id)
    week_start = datetime.utcnow() - timedelta(days=7)
    week_gold = sum(
        int(selected_quest(slot).get("points", 0))
        for slot in slots
        if slot.completed_at and slot.completed_at >= week_start
    )
    action_count = len(slots)
    return {
        "total_gold": user.gold,
        "week_gold": week_gold,
        "current_streak": user.daily_streak,
        "longest_streak": longest_daily_streak(slots),
        "completed_actions": action_count,
        "completed_days": len({slot.completed_at.date() for slot in slots if slot.completed_at}),
        "estimated_kwh": round(action_count * 0.9, 1),
        "estimated_co2_kg": round(action_count * 0.38, 1),
    }


@app.get("/users/me/badges")
def user_badges(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slots = completed_slots(db, user.id)
    values = {
        "actions": len(slots),
        "gold": user.gold,
        "streak": longest_daily_streak(slots),
        "days": len({slot.completed_at.date() for slot in slots if slot.completed_at}),
        "hard": int(any(selected_quest(slot).get("difficulty") == "hard" for slot in slots)),
    }
    badges = []
    for badge_id, icon, name, description, metric, needed in BADGES:
        actual = values[metric]
        have = min(actual, needed)
        badges.append({
            "id": badge_id,
            "icon": icon,
            "name": name,
            "desc": description,
            "have": have,
            "need": needed,
            "earned": actual >= needed,
            "pct": round(have / needed * 100),
        })
    return {"badges": badges, "earned": sum(badge["earned"] for badge in badges)}


@app.get("/users/me/preferences", response_model=Preferences)
def get_preferences(user: models.User = Depends(get_current_user)):
    return {**Preferences().model_dump(), **(user.preferences or {})}


@app.put("/users/me/preferences", response_model=Preferences)
def update_preferences(
    preferences: Preferences,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.preferences = preferences.model_dump()
    db.commit()
    return user.preferences


@app.delete("/users/me/progress", status_code=204)
def reset_progress(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.QuestSlot).filter(models.QuestSlot.user_id == user.id).delete()
    db.query(models.DailyQuest).filter(models.DailyQuest.user_id == user.id).delete()
    user.gold = 0
    user.daily_streak = 0
    user.ecoling_state = "neutral"
    user.last_completed_date = None
    db.commit()


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
    has_predictive_weather = bool(existing and "radar" in (existing.weather_snapshot or {}))
    if existing and (existing.completed or (same_location and has_predictive_weather)):
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
        now=datetime.now(SINGAPORE_TIME),
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
        "message": "Task completed!",
        "gold_earned": gold_earned,
        "user": UserResponse.model_validate(user),
        "completed": True,
        "selected_quest_key": selected_quest["id"],
    }
