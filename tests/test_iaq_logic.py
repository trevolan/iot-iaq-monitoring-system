import unittest

from iaq_logic import assess_air_quality


class TestIAQAssessment(unittest.TestCase):

    def test_good_air_quality(self):
        readings = {
            "co2": 700,
            "pm25": 12,
        }

        result = assess_air_quality(readings)

        self.assertEqual(result["iaq_status"], "Good")
        self.assertFalse(result["alert_active"])

    def test_moderate_co2_condition(self):
        readings = {
            "co2": 800,
            "pm25": 12,
        }

        result = assess_air_quality(readings)

        self.assertEqual(result["iaq_status"], "Moderate")
        self.assertFalse(result["alert_active"])

    def test_poor_co2_condition(self):
        readings = {
            "co2": 1000,
            "pm25": 12,
        }

        result = assess_air_quality(readings)

        self.assertEqual(result["iaq_status"], "Poor")
        self.assertTrue(result["alert_active"])
        self.assertIn(
            "ventilation",
            result["recommendation"].lower(),
        )

    def test_poor_pm25_condition(self):
        readings = {
            "co2": 700,
            "pm25": 35,
        }

        result = assess_air_quality(readings)

        self.assertEqual(result["iaq_status"], "Poor")
        self.assertTrue(result["alert_active"])

    def test_hazardous_co2_condition(self):
        readings = {
            "co2": 2000,
            "pm25": 12,
        }

        result = assess_air_quality(readings)

        self.assertEqual(
            result["iaq_status"],
            "Hazardous",
        )
        self.assertTrue(result["alert_active"])

    def test_hazardous_pm25_condition(self):
        readings = {
            "co2": 700,
            "pm25": 150,
        }

        result = assess_air_quality(readings)

        self.assertEqual(
            result["iaq_status"],
            "Hazardous",
        )
        self.assertTrue(result["alert_active"])


if __name__ == "__main__":
    unittest.main()