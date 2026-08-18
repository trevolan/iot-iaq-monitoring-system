from email_service import send_alert_email


send_alert_email(
    subject="AirSense IQ test notification",
    message=(
        "This is a test notification from your IoT Indoor "
        "Air Quality Monitoring System.\n\n"
        "The Gmail alert connection is working correctly."
    ),
)

print("Test email sent successfully.")