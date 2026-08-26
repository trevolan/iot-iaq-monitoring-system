import unittest
from unittest.mock import patch

from requests import RequestException

from app import app


LIVE_READING = {
    "entry_id": 900,
    "temperature": 24.5,
    "humidity": 55.0,
    "pm1": 8.0,
    "pm25": 14.0,
    "pm10": 20.0,
    "co2": 650.0,
    "device_status": "Online",
    "last_updated": "25 August 2026, 12:00:00",
}


HISTORY = [
    {
        "time": "11:59",
        "temperature": 24.4,
        "humidity": 55.1,
        "pm25": 13.0,
        "co2": 640.0,
    },
    {
        "time": "12:00",
        "temperature": 24.5,
        "humidity": 55.0,
        "pm25": 14.0,
        "co2": 650.0,
    },
]


class TestDashboard(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("app.get_recent_alerts", return_value=[])
    @patch("app.fetch_recent_readings", return_value=HISTORY)
    @patch("app.fetch_latest_readings", return_value=LIVE_READING)
    def test_dashboard_loads_live_data(
        self,
        mock_latest,
        mock_history,
        mock_alerts,
    ):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"Indoor Air Quality Dashboard",
            response.data,
        )
        self.assertIn(
            b"Live ThingSpeak data",
            response.data,
        )
        self.assertIn(b"650.0", response.data)
        self.assertIn(b"Good", response.data)

    @patch("app.get_recent_alerts", return_value=[])
    @patch(
        "app.fetch_latest_readings",
        side_effect=RequestException(
            "ThingSpeak is unavailable"
        ),
    )
    def test_dashboard_uses_demo_fallback(
        self,
        mock_latest,
        mock_alerts,
    ):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"Demonstration data",
            response.data,
        )
        self.assertIn(
            b"Live ThingSpeak data is temporarily unavailable.",
            response.data,
        )


if __name__ == "__main__":
    unittest.main()