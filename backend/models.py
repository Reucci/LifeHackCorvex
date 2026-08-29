from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, nullable=False)

    password_hash = Column(String, nullable=True)

    # Same underlying "gold" column, renamed on the Python side to match the
    # frontend's "totalPoints" concept — no migration needed.
    total_points = Column("gold", Integer, default=0)

    daily_streak = Column(Integer, default=0)

    longest_streak = Column(Integer, default=0)

    ecoling_state = Column(
        String,
        default="neutral"
    )

    last_completed_date = Column(Date, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    habit = Column(String, nullable=False)
    points = Column(Integer, nullable=False)
    difficulty = Column(Float, nullable=False)
    weather_icon = Column(String, nullable=True)
    weather_condition = Column(String, nullable=True)
    weather_temp = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
