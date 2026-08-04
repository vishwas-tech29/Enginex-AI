import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.email.templates import PAYMENT_FAILED_TEMPLATE, WELCOME_EMAIL_TEMPLATE

logger = logging.getLogger("enginex.email")


class EmailService:
    """Sends real SMTP mail when settings.smtp_host is configured. With no
    SMTP server configured (the default in local dev/tests), it logs the
    rendered subject+recipient instead of silently dropping the message —
    mirroring the AI provider router's graceful-degradation pattern
    (app/ai/providers/router.py) rather than faking a delivery."""

    def send(self, to: str, subject: str, html: str) -> bool:
        if not settings.smtp_host:
            logger.info("SMTP not configured — logging email instead of sending. to=%s subject=%r", to, subject)
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = to
        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, [to], message.as_string())
        return True

    def send_welcome(
        self,
        to: str,
        full_name: str,
        plan_tier: str,
        features: list[str],
        trial_ends: str | None = None,
    ) -> bool:
        html = WELCOME_EMAIL_TEMPLATE.render(
            full_name=full_name,
            plan_tier=plan_tier,
            features=features,
            trial_ends=trial_ends,
            dashboard_url=f"{settings.frontend_url}/dashboard",
            support_email=settings.smtp_from_email,
        )
        return self.send(to, "Welcome to Velorah", html)

    def send_payment_failed(self, to: str, full_name: str, amount: float, plan_tier: str) -> bool:
        html = PAYMENT_FAILED_TEMPLATE.render(
            full_name=full_name,
            amount=amount,
            plan_tier=plan_tier,
            billing_url=f"{settings.frontend_url}/dashboard/settings",
        )
        return self.send(to, "Payment failed — action required", html)


email_service = EmailService()
