import unittest
from datetime import datetime, timedelta, timezone

from rules import QUESTS, choose_quests


SINGAPORE_TIME = timezone(timedelta(hours=8))


def observation(value):
    return {"value": value}


def weather(*, temperature=31, humidity=84, rainfall=0, wind=14, condition="Fair", radar=None):
    return {
        "observations": {
            "temperature": observation(temperature),
            "humidity": observation(humidity),
            "rainfall": observation(rainfall),
            "wind_speed": observation(wind),
        },
        "forecast": {"area": "Bishan", "condition": condition},
        "radar": radar or {},
    }


class QuestVarietyTest(unittest.TestCase):
    def test_catalogue_contains_seventeen_live_quests(self):
        self.assertEqual(len(QUESTS), 17)
        self.assertEqual(len({quest["id"] for quest in QUESTS}), 17)

    def test_recent_offers_are_rotated_when_alternatives_fit(self):
        now = datetime(2026, 8, 30, 14, tzinfo=SINGAPORE_TIME)
        current_weather = weather()
        first = choose_quests(current_weather, count=2, seed="slot-1", now=now)
        recent_ids = [quest["id"] for quest in first]
        second = choose_quests(
            current_weather,
            count=2,
            seed="slot-2",
            now=now,
            recent_ids=recent_ids,
        )
        self.assertEqual(len(first), 2)
        self.assertEqual(len(second), 2)
        self.assertNotEqual({quest["id"] for quest in first}, {quest["id"] for quest in second})

    def test_radar_approach_unlocks_rain_preparation(self):
        now = datetime(2026, 8, 30, 16, tzinfo=SINGAPORE_TIME)
        radar = {"movement": "approaching", "eta_minutes": 35, "confidence": "high"}
        offered = choose_quests(weather(radar=radar), count=8, seed="rain", now=now)
        offered_ids = {quest["id"] for quest in offered}
        self.assertIn("bring-laundry-in-before-rain", offered_ids)
        self.assertIn("pre-rain-close-windows", offered_ids)


if __name__ == "__main__":
    unittest.main()
