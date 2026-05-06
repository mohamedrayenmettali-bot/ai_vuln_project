from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import settings


class EmailConfigurationError(RuntimeError):
    pass


class EmailDeliveryError(RuntimeError):
    pass


def is_password_reset_email_configured() -> bool:
    return bool(settings.SMTP_HOST.strip() and settings.SMTP_FROM_EMAIL.strip())


def build_password_reset_url(token: str) -> str:
    template = settings.PASSWORD_RESET_URL_TEMPLATE.strip()
    if "{token}" in template:
        return template.format(token=token)

    separator = "&" if "?" in template else "?"
    return f"{template}{separator}token={token}"


def send_password_reset_email(to_email: str, reset_url: str, expires_in_seconds: int) -> None:
    if not is_password_reset_email_configured():
        raise EmailConfigurationError("SMTP_HOST and SMTP_FROM_EMAIL must be configured for password resets.")

    expires_minutes = max(1, round(expires_in_seconds / 60))
    message = EmailMessage()
    message["Subject"] = "SecureOps password reset"
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message.set_content(
        "\n".join(
            [
                "A password reset was requested for your SecureOps account.",
                "",
                f"Use this link within {expires_minutes} minutes:",
                reset_url,
                "",
                "If you did not request this, you can ignore this email.",
            ]
        )
    )

    try:
        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                _send_message(smtp, message)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                _send_message(smtp, message)
    except smtplib.SMTPException as exc:
        raise EmailDeliveryError("SMTP server rejected the password reset email.") from exc
    except OSError as exc:
        raise EmailDeliveryError("SMTP server could not be reached.") from exc


def _send_message(smtp: smtplib.SMTP, message: EmailMessage) -> None:
    username = settings.SMTP_USERNAME.strip()
    password = settings.SMTP_PASSWORD
    if username:
        smtp.login(username, password)
    smtp.send_message(message)
