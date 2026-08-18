import os
import time

from dotenv import load_dotenv
from requests import RequestException

from alert_store import (
    initialize_database,
    record_alert,
    should_send_alert,
)
from email_service import send_alert_email
from iaq_logic import assess_air_quality
from thingspeak_client import fetch_latest_readings


load_dotenv()


CHECK_INTERVAL = int(
    os.getenv("ALERT_CHECK_INTERVAL_SECONDS", "60")
)

COOLDOWN_MINUTES = int(
    os.getenv("ALERT_COOLDOWN_MINUTES", "30")
)


def create_email_message(readings, assessment):
    """Build the content of an IAQ alert email."""

    return (
        "AirSense IQ detected an indoor air-quality "
        "condition requiring attention.\n\n"
        f"Status: {assessment['iaq_status']}\n"
        f"CO2: {readings['co2']} ppm\n"
        f"PM2.5: {readings['pm25']} ug/m3\n"
        f"Temperature: {readings['temperature']} °C\n"
        f"Humidity: {readings['humidity']} %\n"
        f"Reading time: {readings['last_updated']}\n\n"
        f"Recommended action:\n"
        f"{assessment['recommendation']}\n\n"
        "This is an automated threshold notification "
        "from AirSense IQ."
    )


def check_for_alert():
    """Check the latest reading and send an alert if required."""

    readings = fetch_latest_readings()
    assessment = assess_air_quality(readings)

    print(
        f"Checked entry {readings.get('entry_id')}: "
        f"{assessment['iaq_status']} "
        f"(CO2={readings['co2']} ppm, "
        f"PM2.5={readings['pm25']} ug/m3)"
    )

    if not assessment["alert_active"]:
        print("No email required.")
        return

    if not should_send_alert(
        assessment["iaq_status"],
        COOLDOWN_MINUTES,
    ):
        print("Alert is inside the cooldown period.")
        return

    subject = (
        f"AirSense IQ Alert: "
        f"{assessment['iaq_status']} air quality"
    )

    send_alert_email(
        subject,
        create_email_message(readings, assessment),
    )

    record_alert(readings, assessment)

    print("Alert email sent and recorded.")


def main():
    """Run the alert monitor continuously."""

    initialize_database()

    print("AirSense IQ email monitor started.")
    print(
        f"Checking ThingSpeak every "
        f"{CHECK_INTERVAL} seconds."
    )

    try:
        while True:
            try:
                check_for_alert()

            except (
                RequestException,
                ValueError,
                KeyError,
                OSError,
            ) as error:
                print(f"Monitoring error: {error}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nAirSense IQ monitor stopped.")


if __name__ == "__main__":
    main()