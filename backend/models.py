from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, nullable=False)

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