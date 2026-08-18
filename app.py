from datetime import datetime

from flask import Flask, render_template


app = Flask(__name__)


@app.route("/")
def dashboard():
    # Temporary sample readings used while the dashboard is being developed.
    readings = {
        "temperature": 24.6,
        "humidity": 54.2,
        "pm1": 8,
        "pm25": 14,
        "pm10": 20,
        "co2": 720,
        "iaq_status": "Good",
        "device_status": "Online",
    }

    last_updated = datetime.now().strftime("%d %B %Y, %H:%M:%S")

    return render_template(
        "index.html",
        readings=readings,
        last_updated=last_updated,
    )


if __name__ == "__main__":
    app.run(debug=True)