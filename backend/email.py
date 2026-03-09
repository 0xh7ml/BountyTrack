# backend/email.py
"""
Centralised email sending via Resend (https://resend.com).
Usage:
    from .email import send_invitation_email
    send_invitation_email(to_email, accept_url, expiry_days)
"""
import resend
from django.conf import settings


def send_invitation_email(to_email: str, accept_url: str, expiry_days: int = 7) -> dict:
    """
    Send a user-invitation email via Resend.
    Returns the Resend API response.
    Raises ValueError if RESEND_API_KEY is not configured.
    """
    api_key = getattr(settings, 'RESEND_API_KEY', '')
    if not api_key:
        raise ValueError("RESEND_API_KEY is not set. Add it to your .env file.")

    resend.api_key = api_key

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#343a40;">You've been invited to <span style="color:#007bff;">Bounty Track</span></h2>
      <p>You have been invited to join the Bounty Track platform.</p>
      <p>Click the button below to accept your invitation and set up your account:</p>
      <p style="text-align:center;margin:32px 0;">
        <a href="{accept_url}"
           style="background:#007bff;color:#fff;padding:12px 28px;border-radius:6px;
                  text-decoration:none;font-weight:bold;font-size:15px;">
          Accept Invitation
        </a>
      </p>
      <p style="color:#6c757d;font-size:13px;">
        Or copy and paste this link into your browser:<br>
        <a href="{accept_url}" style="color:#007bff;">{accept_url}</a>
      </p>
      <hr style="border:none;border-top:1px solid #dee2e6;margin:24px 0;">
      <p style="color:#6c757d;font-size:12px;">
        This invitation expires in <strong>{expiry_days} day(s)</strong>.
        If you did not expect this email, you can safely ignore it.
      </p>
    </div>
    """

    text_body = (
        f"You've been invited to Bounty Track.\n\n"
        f"Accept your invitation here:\n{accept_url}\n\n"
        f"This link expires in {expiry_days} day(s)."
    )

    params: resend.Emails.SendParams = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to":   [to_email],
        "subject": "You've been invited to Bounty Track",
        "html": html_body,
        "text": text_body,
    }
    return resend.Emails.send(params)
