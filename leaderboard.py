# Drop into LifeHackCorvex: backend/leaderboard.py
#
# Three boards:
#   GET /leaderboard          - all-time, ranked by User.gold (already tracked)
#   GET /leaderboard/daily    - ranked by points earned in the last 24h
#   GET /leaderboard/weekly   - ranked by points earned in the last 7 days
#
# User.gold is a running total with no dates attached, so there's no way to
# recover "how many points did they earn today/this week" from it alone.
# PointLog below is a minimal per-completion record (user_id, points,
# earned_at) that the daily/weekly boards aggregate over - see
# INTEGRATION.md for the one-line change to backend/main.py's
# /actions/complete that writes to it.
#
# Public - no login required to view any board; the frontend highlights the
# signed-in user's own row client-side.

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, DateTime, ForeignKey, Integer, desc, func
from sqlalchemy.orm import Session

import models
from database import Base, SessionLocal, engine

router = APIRouter()

MAX_LIMIT = 100


class PointLog(Base):
    """One row per point-earning completion, so daily/weekly totals can be
    computed. Independent of User.gold (which just accumulates forever).
    """

    __tablename__ = "point_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    points = Column(Integer, nullable=False)
    earned_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Defined after main.py's own Base.metadata.create_all(), so make sure this
# table exists too regardless of import order. create_all is a no-op for
# tables that already exist.
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    username: str
    gold: int
    daily_streak: int


class PeriodLeaderboardEntry(BaseModel):
    rank: int
    username: str
    points: int


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    limit = max(1, min(limit, MAX_LIMIT))

    users = (
        db.query(models.User)
        .order_by(desc(models.User.gold), models.User.created_at.asc())
        .limit(limit)
        .all()
    )

    return [
        LeaderboardEntry(
            rank=i + 1,
            username=u.username,
            gold=u.gold,
            daily_streak=u.daily_streak,
        )
        for i, u in enumerate(users)
    ]


def _points_leaderboard(db: Session, since: datetime, limit: int) -> List[PeriodLeaderboardEntry]:
    limit = max(1, min(limit, MAX_LIMIT))

    rows = (
        db.query(
            models.User.username,
            func.sum(PointLog.points).label("points"),
        )
        .join(PointLog, PointLog.user_id == models.User.id)
        .filter(PointLog.earned_at >= since)
        .group_by(models.User.id)
        .having(func.sum(PointLog.points) > 0)
        .order_by(desc("points"))
        .limit(limit)
        .all()
    )

    return [
        PeriodLeaderboardEntry(rank=i + 1, username=username, points=int(points))
        for i, (username, points) in enumerate(rows)
    ]


@router.get("/leaderboard/daily", response_model=List[PeriodLeaderboardEntry])
def get_daily_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    """Ranks users by points earned in the last 24 hours, highest first."""
    since = datetime.utcnow() - timedelta(days=1)
    return _points_leaderboard(db, since, limit)


@router.get("/leaderboard/weekly", response_model=List[PeriodLeaderboardEntry])
def get_weekly_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    """Ranks users by points earned in the last 7 days, highest first."""
    since = datetime.utcnow() - timedelta(days=7)
    return _points_leaderboard(db, since, limit)
