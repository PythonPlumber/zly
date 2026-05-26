from datetime import datetime, timezone

from app.config import settings
from app.core.email import get_email_backend
from app.core.logging import get_logger

logger = get_logger(__name__)

_INVITE_EMAIL_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <h2 style="color: #333;">You've been invited to {workspace_name}</h2>
  <p>{invited_by_name} has invited you to join <strong>{workspace_name}</strong> on Zly.</p>
  <p>Click the button below to accept your invitation:</p>
  <div style="text-align: center; margin: 30px 0;">
    <a href="{invite_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Accept Invitation</a>
  </div>
  <p style="color: #666; font-size: 14px;">This invitation expires in 7 days ({expires_at}).</p>
  <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
  <p style="color: #999; font-size: 12px;">If you didn't expect this email, you can safely ignore it.</p>
</body>
</html>"""

_PASSWORD_RESET_EMAIL_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <h2 style="color: #333;">Reset your password</h2>
  <p>We received a request to reset your password for your Zly account.</p>
  <p>Click the button below to set a new password:</p>
  <div style="text-align: center; margin: 30px 0;">
    <a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
  </div>
  <p style="color: #666; font-size: 14px;">This link expires in 1 hour ({expires_at}).</p>
  <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
  <p style="color: #999; font-size: 12px;">If you didn't request a password reset, you can safely ignore this email. Your password won't change until you create a new one.</p>
</body>
</html>"""

_EXPIRY_ALERT_EMAIL_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <h2 style="color: #333;">Link expiring soon: {link_title}</h2>
  <p>Your short link <strong>{short_code}</strong> is set to expire in <strong>{hours_remaining} hours</strong>.</p>
  <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
    <tr><td style="padding: 8px; border: 1px solid #eee;"><strong>Short URL</strong></td><td style="padding: 8px; border: 1px solid #eee;"><a href="{short_url}">{short_url}</a></td></tr>
    <tr><td style="padding: 8px; border: 1px solid #eee;"><strong>Destination</strong></td><td style="padding: 8px; border: 1px solid #eee;"><a href="{destination_url}">{destination_url}</a></td></tr>
    <tr><td style="padding: 8px; border: 1px solid #eee;"><strong>Expires at</strong></td><td style="padding: 8px; border: 1px solid #eee;">{expires_at}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #eee;"><strong>Total clicks</strong></td><td style="padding: 8px; border: 1px solid #eee;">{total_clicks}</td></tr>
  </table>
  <p>If you want to keep this link active, please update or remove the expiration date in your Zly dashboard.</p>
  <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
  <p style="color: #999; font-size: 12px;">This is an automated alert from Zly.</p>
</body>
</html>"""


async def send_invite_email(
    invite_id: str,
    to_email: str,
    workspace_name: str,
    invited_by_name: str,
    invite_url: str,
    expires_at: str,
) -> dict:
    backend = get_email_backend()
    html = _INVITE_EMAIL_HTML.format(
        workspace_name=workspace_name,
        invited_by_name=invited_by_name,
        invite_url=invite_url,
        expires_at=expires_at,
    )
    logger.info("Sending invite email", extra={"invite_id": invite_id, "to": to_email})
    return await backend.send_email(
        to=to_email,
        subject=f"You've been invited to {workspace_name}",
        html_body=html,
    )


async def send_password_reset_email(
    user_id: str,
    to_email: str,
    reset_url: str,
    expires_at: str,
) -> dict:
    backend = get_email_backend()
    html = _PASSWORD_RESET_EMAIL_HTML.format(
        reset_url=reset_url,
        expires_at=expires_at,
    )
    logger.info("Sending password reset email", extra={"user_id": user_id, "to": to_email})
    return await backend.send_email(
        to=to_email,
        subject="Reset your Zly password",
        html_body=html,
    )


async def send_expiry_alert_email(
    link_id: str,
    to_email: str,
    link_title: str,
    short_code: str,
    short_url: str,
    destination_url: str,
    expires_at: str,
    hours_remaining: int,
    total_clicks: int,
) -> dict:
    backend = get_email_backend()
    html = _EXPIRY_ALERT_EMAIL_HTML.format(
        link_title=link_title,
        short_code=short_code,
        short_url=short_url,
        destination_url=destination_url,
        expires_at=expires_at,
        hours_remaining=hours_remaining,
        total_clicks=total_clicks,
    )
    logger.info("Sending expiry alert email", extra={"link_id": link_id, "to": to_email})
    return await backend.send_email(
        to=to_email,
        subject=f"Link expiring soon: {link_title}",
        html_body=html,
    )