from datetime import datetime

from flask import Flask, render_template
from requests import RequestException

from thingspeak_client import fetch_latest_readings


app = Flask(__name__)


DEMO_READINGS = {
    "temperature": 24.6,
    "humidity": 54.2,
    "pm1": 8,
    "pm25": 14,
    "pm10": 20,
    "co2": 720,
    "device_status": "Unavailable",
}


def assess_air_quality(readings):
    """Classify the readings using configured project alert thresholds."""

    co2 = readings["co2"]
    pm25 = readings["pm25"]

    if co2 >= 2000 or pm25 >= 150:
        return {
            "iaq_status": "Hazardous",
            "status_class": "hazardous",
            "alert_active": True,
            "alert_title": "Immediate attention required",
            "recommendation": (
                "Leave the affected area temporarily, improve ventilation "
                "and investigate the likely pollution source."
            ),
        }

    if co2 >= 1000 or pm25 >= 35:
        if co2 >= 1000 and pm25 >= 35:
            action = (
                "Increase ventilation and investigate possible indoor "
                "particle sources."
            )
        elif co2 >= 1000:
            action = (
                "Open available windows or doors for 10–15 minutes "
                "to improve ventilation."
            )
        else:
            action = (
                "Reduce possible particle sources and use an extractor "
                "or suitable ventilation where available."
            )

        return {
            "iaq_status": "Poor",
            "status_class": "poor",
            "alert_active": True,
            "alert_title": "Air quality requires action",
            "recommendation": action,
        }

    if co2 >= 800 or pm25 >= 20:
        return {
            "iaq_status": "Moderate",
            "status_class": "moderate",
            "alert_active": False,
            "alert_title": "Continue monitoring conditions",
            "recommendation": (
                "Consider improving ventilation and continue monitoring "
                "for any further increase."
            ),
        }

    return {
        "iaq_status": "Good",
        "status_class": "good",
        "alert_active": False,
        "alert_title": "No immediate action required",
        "recommendation": (
            "Continue normal room use and ventilation. The system will "
            "notify you if conditions deteriorate."
        ),
    }


@app.route("/")
def dashboard():
    connection_error = None

    try:
        readings = fetch_latest_readings()
        last_updated = readings.pop("last_updated")
        data_source = "Live ThingSpeak data"

    except (RequestException, ValueError, KeyError) as error:
        app.logger.warning("ThingSpeak connection failed: %s", error)

        readings = DEMO_READINGS.copy()
        last_updated = datetime.now().strftime(
            "%d %B %Y, %H:%M:%S"
        )
        data_source = "Demonstration data"
        connection_error = (
            "Live ThingSpeak data is temporarily unavailable."
        )

    readings.update(assess_air_quality(readings))

    return render_template(
        "index.html",
        readings=readings,
        last_updated=last_updated,
        data_source=data_source,
        connection_error=connection_error,
    )


if __name__ == "__main__":
    app.run(debug=True)