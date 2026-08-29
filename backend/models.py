from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, nullable=False)

    password_hash = Column(String, nullable=True)

    gold = Column(Integer, default=0)

    daily_streak = Column(Integer, default=0)

    ecoling_state = Column(
        String,
        default="neutral"
    )

    last_completed_date = Column(Date, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyQuest(Base):
    __tablename__ = "daily_quests"
    __table_args__ = (UniqueConstraint("user_id", "quest_date", name="uq_user_daily_quest"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    quest_date = Column(Date, nullable=False, index=True)
    quest_key = Column(String, nullable=False)
    quest_payload = Column(JSON, nullable=False)
    weather_snapshot = Column(JSON, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuestSlot(Base):
    __tablename__ = "quest_slots"
    __table_args__ = (UniqueConstraint("user_id", "slot_start", name="uq_user_quest_slot"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    slot_start = Column(DateTime, nullable=False, index=True)
    slot_end = Column(DateTime, nullable=False)
    quest_options = Column(JSON, nullable=False)
    weather_snapshot = Column(JSON, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    selected_quest_key = Column(String, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
