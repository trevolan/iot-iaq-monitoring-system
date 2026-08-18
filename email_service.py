import os
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


def send_alert_email(subject, message):
    """Send an AirSense IQ alert using secure Gmail SMTP."""

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USERNAME")
    app_password = os.getenv("SMTP_APP_PASSWORD")
    recipient = os.getenv("ALERT_RECIPIENT")

    required_settings = {
        "SMTP_HOST": smtp_host,
        "SMTP_PORT": smtp_port,
        "SMTP_USERNAME": username,
        "SMTP_APP_PASSWORD": app_password,
        "ALERT_RECIPIENT": recipient,
    }

    missing_settings = [
        name
        for name, value in required_settings.items()
        if not value
    ]

    if missing_settings:
        missing_names = ", ".join(missing_settings)

        raise ValueError(
            f"Missing email settings: {missing_names}"
        )

    email = EmailMessage()
    email["From"] = username
    email["To"] = recipient
    email["Subject"] = subject
    email.set_content(message)

    secure_context = ssl.create_default_context()

    with smtplib.SMTP(
        smtp_host,
        int(smtp_port),
        timeout=20,
    ) as server:
        server.ehlo()
        server.starttls(context=secure_context)
        server.ehlo()
        server.login(username, app_password)
        server.send_message(email)