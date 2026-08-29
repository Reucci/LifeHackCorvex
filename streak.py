"""Tracks quests completed consecutively and awards a one-time achievement
every time the streak reaches a new multiple of 10."""

import math

STREAK_MILESTONE = 10
STREAK_BONUS_BASE = 50


def calculate_streak_bonus(streak):
    """Bonus gold for the nth ten-streak reached (n = streak // 10).

    bonus = 50 * n + log_1.5(n). Returns 0 for any streak that isn't a
    positive multiple of STREAK_MILESTONE.
    """
    if streak <= 0 or streak % STREAK_MILESTONE != 0:
        return 0.0
    n = streak // STREAK_MILESTONE
    return round(STREAK_BONUS_BASE * n + math.log(n, 1.5), 2)


def build_achievement(streak):
    """Achievement payload for a streak that just hit a multiple of 10."""
    return {
        "streak": streak,
        "title": f"{streak}-Quest Streak",
        "bonus": calculate_streak_bonus(streak),
    }


class StreakTracker:
    """Counts quests completed back-to-back and hands out a one-time
    achievement each time the streak reaches a new multiple of 10.

    Missing a quest resets the streak counter but not previously earned
    achievements - an achievement is never awarded twice, even if the
    streak is broken and later climbs back through the same milestone.
    """

    def __init__(self, streak=0, achieved_milestones=None):
        self.streak = streak
        self.achieved_milestones = set(achieved_milestones or ())

    def complete_quest(self):
        """Record one completed quest.

        :returns: (streak, achievement) - achievement is None unless this
            completion just landed the streak on a new multiple of 10 that
            hasn't already been achieved.
        """
        self.streak += 1
        achievement = None

        if self.streak % STREAK_MILESTONE == 0:
            milestone = self.streak // STREAK_MILESTONE
            if milestone not in self.achieved_milestones:
                self.achieved_milestones.add(milestone)
                achievement = build_achievement(self.streak)

        return self.streak, achievement

    def miss_quest(self):
        """Break the streak (a quest was skipped or missed)."""
        self.streak = 0
        return self.streak
