import os
import tempfile
import unittest
from datetime import datetime

database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
database_file.close()
os.environ["ECOLINGS_DATABASE_URL"] = "sqlite:///" + database_file.name.replace("\\", "/")

from fastapi.testclient import TestClient

import models
from database import SessionLocal, engine
from main import app, current_quest_slot


class IntegratedAccountApiTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        os.unlink(database_file.name)

    def test_account_progress_contract(self):
        client = TestClient(app)
        auth = client.post("/auth/register", json={
            "username": "IntegrationUser",
            "password": "securepass123",
        })
        self.assertEqual(auth.status_code, 201, auth.text)
        payload = auth.json()
        headers = {"Authorization": f"Bearer {payload['token']}"}

        preferences = {
            "display_name": "Green Tester",
            "reminders": True,
            "reminder_time": "08:30",
            "sound": False,
            "units": "metric",
        }
        saved = client.put("/users/me/preferences", headers=headers, json=preferences)
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(client.get("/users/me/preferences", headers=headers).json(), preferences)

        slot_start, slot_end = current_quest_slot()
        db = SessionLocal()
        db.add(models.QuestSlot(
            user_id=payload["user"]["id"],
            slot_start=slot_start.replace(tzinfo=None),
            slot_end=slot_end.replace(tzinfo=None),
            quest_options=[{
                "id": "unplug-idle-devices",
                "title": "Unplug three idle devices",
                "description": "Test quest",
                "points": 8,
                "difficulty": "medium",
            }],
            weather_snapshot={
                "observations": {"temperature": {"value": 30}},
                "forecast": {"condition": "Fair", "area": "Bishan"},
            },
        ))
        db.commit()
        slot = db.query(models.QuestSlot).first()
        quest_id = slot.id
        db.close()

        completed = client.post("/actions/complete", headers=headers, json={
            "quest_id": quest_id,
            "quest_key": "unplug-idle-devices",
        })
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(completed.json()["gold_earned"], 8)

        history = client.get("/quests/history", headers=headers).json()
        stats = client.get("/users/me/stats", headers=headers).json()
        badges = client.get("/users/me/badges", headers=headers).json()
        self.assertEqual(history["entries"][0]["habit"], "Unplug three idle devices")
        self.assertEqual(stats["total_gold"], 8)
        self.assertEqual(stats["completed_actions"], 1)
        self.assertTrue(next(b for b in badges["badges"] if b["id"] == "first-step")["earned"])

        reset = client.delete("/users/me/progress", headers=headers)
        self.assertEqual(reset.status_code, 204, reset.text)
        self.assertEqual(client.get("/users/me/stats", headers=headers).json()["completed_actions"], 0)


if __name__ == "__main__":
    unittest.main()
