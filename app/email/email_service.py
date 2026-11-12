
import os
import ssl
import smtplib
import logging

from pathlib import Path
from email.message import EmailMessage
from dotenv import load_dotenv


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load credentials from .env
load_dotenv(PROJECT_ROOT / ".env")


# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


class EmailService:
    """Professional Gmail SMTP email service."""

    def __init__(self):

        self.sender_email = os.getenv("GMAIL_ADDRESS")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")

        self.smtp_host = os.getenv(
            "SMTP_HOST",
            "smtp.gmail.com"
        )

        self.smtp_port = int(
            os.getenv("SMTP_PORT", "587")
        )

        if not self.sender_email or not self.app_password:
            raise ValueError(
                "Gmail credentials are missing. Check your .env file."
            )

    def send_email(
        self,
        to_email,
        subject,
        html_body,
        text_body=None
    ):
        """Send an HTML email securely through Gmail SMTP."""

        if not to_email or "@" not in to_email:
            raise ValueError("A valid recipient email is required.")

        message = EmailMessage()

        message["From"] = self.sender_email
        message["To"] = to_email
        message["Subject"] = subject

        # Plain-text fallback
        message.set_content(
            text_body or "Please view this email in an HTML-compatible email client."
        )

        # HTML email content
        message.add_alternative(
            html_body,
            subtype="html"
        )

        try:

            logger.info("Connecting to Gmail SMTP server...")

            context = ssl.create_default_context()

            with smtplib.SMTP(
                self.smtp_host,
                self.smtp_port,
                timeout=30
            ) as server:

                server.ehlo()

                server.starttls(context=context)

                server.ehlo()

                server.login(
                    self.sender_email,
                    self.app_password
                )

                server.send_message(message)

            logger.info(
                "Email successfully sent to %s",
                to_email
            )

            return True

        except Exception:

            logger.exception("Email delivery failed.")

            raise


if __name__ == "__main__":

    email_service = EmailService()

    result = email_service.send_email(
        to_email=email_service.sender_email,
        subject="MeetFlow AI - Email Service Test",
        html_body="""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>MeetFlow AI Email Service</h2>
                <p>Congratulations!</p>
                <p>Your Gmail SMTP integration is working successfully.</p>
                <p>This is your first automated test email.</p>
                <br>
                <strong>MeetFlow AI</strong>
                <p>Intelligent Meeting & Task Automation</p>
            </body>
        </html>
        """,
        text_body=(
            "MeetFlow AI Gmail integration is working successfully."
        )
    )

    if result:
        print("\nTest email sent successfully!")
