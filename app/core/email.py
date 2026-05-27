import asyncio
from typing import Any

from email.base64mime import body_encode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_email_backend: "EmailBackend | None" = None


class EmailBackend:
    def __init__(
        self,
        host: str = "",
        port: int = 587,
        username: str = "",
        password: str = "",
        from_email: str = "",
        from_name: str = "",
        use_tls: bool = True,
    ) -> None:
        self.host = host or settings.smtp_host
        self.port = port or settings.smtp_port
        self.username = username or settings.smtp_user
        self.password = password or settings.smtp_password
        self.from_email = from_email or settings.smtp_from
        self.from_name = from_name or settings.smtp_from_name
        self.use_tls = use_tls

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        html_body: str,
        text_body: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
    ) -> dict[str, Any]:
        if isinstance(to, list):
            recipients = to
        else:
            recipients = [to]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._format_from(from_email, from_name)
        msg["To"] = ", ".join(recipients)

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            import aiosmtplib
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls,
                start_tls=True,
            )
            logger.info("Email sent", extra={"to": recipients, "subject": subject})
            return {"status": "sent", "to": recipients}
        except Exception as exc:
            logger.error("Email send failed", extra={"to": recipients, "subject": subject, "error": str(exc)})
            return {"status": "failed", "to": recipients, "error": str(exc)}

    def _format_from(self, from_email: str | None, from_name: str | None) -> str:
        email = from_email or self.from_email
        name = from_name or self.from_name
        if name:
            return f"{name} <{email}>"
        return email


def get_email_backend() -> EmailBackend:
    global _email_backend
    if _email_backend is None:
        _email_backend = EmailBackend()
    return _email_backend