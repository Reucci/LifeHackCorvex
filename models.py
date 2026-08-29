from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text

from db import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    product_stock = Column(Integer, nullable=False, default=0)
    product_desc = Column(Text)
    product_cost = Column(Float, nullable=False)


class Award(Base):
    """Catalog of awards the weather-to-quest API can grant, e.g. via
    streak.py (hitting a 50-quest streak) or daily/first-quest milestones
    tracked elsewhere in the app.
    """

    __tablename__ = "awards"

    award_id = Column(Integer, primary_key=True, index=True)
    award_name = Column(String, nullable=False)
    award_desc = Column(Text)
    # How the award is earned, e.g. "streak", "daily_streak", "first_quest".
    award_type = Column(String, nullable=False)
    # The number that unlocks it: 50 for a 50-streak, 14 for a 14-day daily
    # streak, 1 for completing your first quest.
    threshold = Column(Integer, nullable=False)
    gold_reward = Column(Float, nullable=False, default=0)


class UserStreak(Base):
    """Per-user streak state, persisted across requests since the API
    itself is stateless. Mirrors streak.py's StreakTracker plus a
    calendar-day streak and a lifetime completion count.
    """

    __tablename__ = "user_streaks"

    user_id = Column(String, primary_key=True)
    current_streak = Column(Integer, nullable=False, default=0)
    total_completed = Column(Integer, nullable=False, default=0)
    daily_streak = Column(Integer, nullable=False, default=0)
    last_completed_date = Column(Date, nullable=True)


class UserAward(Base):
    """One row per award actually granted to a user - prevents the same
    award from being handed out twice.
    """

    __tablename__ = "user_awards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    award_id = Column(Integer, ForeignKey("awards.award_id"), nullable=False)
    earned_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
