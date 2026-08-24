import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

def send_verification_email(receiver_email, otp):

    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    message = EmailMessage()

    message["Subject"] = "Task Manager - Email Verification"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.set_content(f"""
Hello,

Your Task Manager email verification OTP is:

{otp}

This OTP will expire in 10 minutes.

If you did not create this account, you can ignore this email.

Regards,
Task Manager
""")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            sender_email,
            sender_password
        )

        server.send_message(message)

    return True


