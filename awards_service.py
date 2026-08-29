"""Wires streak.py's streak logic into the database: persists per-user
streak state across requests and grants awards from the `awards` catalog
the first time a user crosses their threshold.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from models import Award, UserAward, UserStreak
from streak import calculate_streak_bonus

DEFAULT_AWARDS = [
    {
        "award_name": "50-Quest Streak",
        "award_desc": "Complete 50 quests back-to-back.",
        "award_type": "streak",
        "threshold": 50,
        "gold_reward": calculate_streak_bonus(50),
    },
    {
        "award_name": "14-Day Streak",
        "award_desc": "Complete at least one quest every day for 14 days straight.",
        "award_type": "daily_streak",
        "threshold": 14,
        "gold_reward": 140.0,
    },
    {
        "award_name": "First Quest",
        "award_desc": "Complete your very first quest.",
        "award_type": "first_quest",
        "threshold": 1,
        "gold_reward": 10.0,
    },
]


def seed_default_awards(session: Session):
    """Insert the default award catalog if it isn't there yet. Safe to call
    on every app startup - only fills in rows that don't already exist.
    """
    existing_types = {a.award_type for a in session.query(Award).all()}
    for entry in DEFAULT_AWARDS:
        if entry["award_type"] not in existing_types:
            session.add(Award(**entry))
    session.commit()


def _get_or_create_user_streak(session: Session, user_id: str) -> UserStreak:
    user_streak = session.get(UserStreak, user_id)
    if user_streak is None:
        # Explicit zeros: column defaults only apply once the row is
        # flushed, but we read/increment these fields immediately below.
        user_streak = UserStreak(
            user_id=user_id,
            current_streak=0,
            total_completed=0,
            daily_streak=0,
        )
        session.add(user_streak)
    return user_streak


def _grant_if_new(session: Session, user_id: str, award: Award, awards_earned: list):
    already_earned = (
        session.query(UserAward)
        .filter_by(user_id=user_id, award_id=award.award_id)
        .first()
    )
    if already_earned is None:
        session.add(UserAward(user_id=user_id, award_id=award.award_id))
        awards_earned.append({
            "award_id": award.award_id,
            "award_name": award.award_name,
            "award_type": award.award_type,
            "gold_reward": award.gold_reward,
        })


def record_completion(session: Session, user_id: str) -> dict:
    """Record that `user_id` completed a quest right now: bumps their
    consecutive-quest streak, their calendar-day streak, and their lifetime
    total, then grants any award whose threshold was just reached.

    :returns: {"user_id", "streak", "daily_streak", "total_completed", "awards_earned"}
    """
    user_streak = _get_or_create_user_streak(session, user_id)

    today = date.today()
    user_streak.current_streak += 1
    user_streak.total_completed += 1

    if user_streak.last_completed_date == today:
        pass  # already completed a quest today; daily streak unchanged
    elif user_streak.last_completed_date == today - timedelta(days=1):
        user_streak.daily_streak += 1
    else:
        user_streak.daily_streak = 1
    user_streak.last_completed_date = today

    awards_earned = []
    matching_awards = (
        session.query(Award)
        .filter(
            (
                (Award.award_type == "streak")
                & (Award.threshold == user_streak.current_streak)
            )
            | (
                (Award.award_type == "daily_streak")
                & (Award.threshold == user_streak.daily_streak)
            )
            | (
                (Award.award_type == "first_quest")
                & (Award.threshold == user_streak.total_completed)
            )
        )
        .all()
    )
    for award in matching_awards:
        _grant_if_new(session, user_id, award, awards_earned)

    session.commit()

    return {
        "user_id": user_id,
        "streak": user_streak.current_streak,
        "daily_streak": user_streak.daily_streak,
        "total_completed": user_streak.total_completed,
        "awards_earned": awards_earned,
    }


def reset_streak(session: Session, user_id: str) -> dict:
    """Break a user's consecutive-quest streak (a quest was skipped or
    missed). Daily streak and lifetime total are untouched.
    """
    user_streak = _get_or_create_user_streak(session, user_id)
    user_streak.current_streak = 0
    session.commit()
    return {"user_id": user_id, "streak": user_streak.current_streak}
