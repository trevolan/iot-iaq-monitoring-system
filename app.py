from datetime import datetime

from flask import Flask, render_template
from requests import RequestException

from iaq_logic import assess_air_quality
from thingspeak_client import (
    fetch_latest_readings,
    fetch_recent_readings,
)


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


@app.route("/")
def dashboard():
    connection_error = None

    try:
        readings = fetch_latest_readings()
        history = fetch_recent_readings(results=30)
        last_updated = readings.pop("last_updated")
        data_source = "Live ThingSpeak data"

    except (RequestException, ValueError, KeyError) as error:
        app.logger.warning("ThingSpeak connection failed: %s", error)

        readings = DEMO_READINGS.copy()
        history = []
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
        history=history,
        last_updated=last_updated,
        data_source=data_source,
        connection_error=connection_error,
    )


if __name__ == "__main__":
    app.run(debug=True)