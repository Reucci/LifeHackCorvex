from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
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
