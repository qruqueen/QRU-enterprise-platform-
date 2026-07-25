"""QRU transactional email — provider abstraction (Resend) + branded templates.

Design rules (Founder-approved):
- The QRU confirmation is the customer's durable delivery/recovery record. It is SEPARATE from
  any Stripe payment receipt.
- The Resend API key is read from the environment only and is NEVER printed, logged or returned.
- A provider "accepted/queued" response is recorded as `sent-to-provider`, NOT as confirmed inbox
  delivery. We only claim delivery if the provider explicitly reports it (Resend's send call does
  not — it returns an id meaning accepted for delivery).
- If no provider is configured, sending is `skipped` and the order/fulfillment is never affected.
"""
import os
import asyncio
import logging

logger = logging.getLogger("qru_email")

# Brand palette (matches the public storefront)
_INK = "#1C1C1A"
_GOLD = "#C5A059"
_PAPER = "#FAFAF8"
_MUTED = "#575754"


def provider_configured() -> bool:
    return bool(os.environ.get("RESEND_API_KEY"))


def sender() -> str:
    return os.environ.get("SENDER_EMAIL") or "QRU Press <onboarding@resend.dev>"


def support_email() -> str:
    return os.environ.get("SUPPORT_EMAIL") or "support@qru-online.com"


async def send_confirmation(*, to: str, subject: str, html: str) -> dict:
    """Send one transactional email. Returns a status dict; never raises.

    status is one of:
      - "sent-to-provider": provider accepted the message (message id captured)
      - "failed": provider rejected / errored (sanitized reason captured)
      - "skipped": no provider configured (order still fulfilled)
    """
    if not provider_configured():
        return {"status": "skipped", "provider": "resend", "provider_message_id": None,
                "error": "email provider not configured"}
    try:
        import resend
        resend.api_key = os.environ["RESEND_API_KEY"]
        params = {"from": sender(), "to": [to], "subject": subject, "html": html,
                  "reply_to": support_email()}
        res = await asyncio.to_thread(resend.Emails.send, params)
        mid = res.get("id") if isinstance(res, dict) else getattr(res, "id", None)
        return {"status": "sent-to-provider", "provider": "resend",
                "provider_message_id": mid, "error": None}
    except Exception as e:  # sanitized — never surface the key or full payload
        logger.error("QRU confirmation email send failed: %s", type(e).__name__)
        return {"status": "failed", "provider": "resend", "provider_message_id": None,
                "error": (str(e) or type(e).__name__)[:200]}


def render_confirmation_html(*, book_title: str, amount: float, currency: str,
                             purchase_date: str, order_ref: str, access_url: str,
                             expires_str: str, download_max: int) -> str:
    """QRU-branded HTML (inline CSS, table layout — email-client safe)."""
    cur = (currency or "usd").upper()
    amount_str = f"${amount:,.2f} {cur}"
    support = support_email()
    return f"""<!doctype html>
<html>
<body style="margin:0;padding:0;background:{_PAPER};font-family:Georgia,'Times New Roman',serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_PAPER};padding:32px 0;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border:1px solid #ECECE6;border-radius:14px;overflow:hidden;">
        <tr><td style="background:{_INK};padding:28px 36px;">
          <div style="color:{_GOLD};font-size:11px;letter-spacing:3px;text-transform:uppercase;">QRU Press&trade; &middot; Treasure Standard&trade;</div>
          <div style="color:{_PAPER};font-size:24px;margin-top:8px;">Your purchase is confirmed</div>
        </td></tr>
        <tr><td style="padding:32px 36px 8px 36px;">
          <p style="color:#0a7d2c;font-size:15px;margin:0 0 18px 0;font-family:Arial,Helvetica,sans-serif;font-weight:bold;">&#10004;&nbsp;Payment successful</p>
          <p style="color:{_INK};font-size:16px;margin:0 0 22px 0;">Thank you. Your copy of
             <strong>{book_title}</strong> is ready. Use the secure link below to download it.</p>

          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:{_MUTED};border-top:1px solid #ECECE6;">
            <tr><td style="padding:12px 0;border-bottom:1px solid #F3F3EE;">Product</td><td align="right" style="padding:12px 0;border-bottom:1px solid #F3F3EE;color:{_INK};">{book_title}</td></tr>
            <tr><td style="padding:12px 0;border-bottom:1px solid #F3F3EE;">Amount paid</td><td align="right" style="padding:12px 0;border-bottom:1px solid #F3F3EE;color:{_INK};">{amount_str}</td></tr>
            <tr><td style="padding:12px 0;border-bottom:1px solid #F3F3EE;">Purchase date</td><td align="right" style="padding:12px 0;border-bottom:1px solid #F3F3EE;color:{_INK};">{purchase_date}</td></tr>
            <tr><td style="padding:12px 0;border-bottom:1px solid #F3F3EE;">Purchase reference</td><td align="right" style="padding:12px 0;border-bottom:1px solid #F3F3EE;color:{_INK};">{order_ref}</td></tr>
          </table>

          <div style="text-align:center;margin:30px 0 14px 0;">
            <a href="{access_url}" style="background:{_INK};color:{_PAPER};text-decoration:none;font-family:Arial,Helvetica,sans-serif;font-size:15px;padding:14px 34px;border-radius:999px;display:inline-block;">Access your book &rarr;</a>
          </div>
          <p style="color:{_MUTED};font-size:13px;font-family:Arial,Helvetica,sans-serif;text-align:center;margin:0 0 26px 0;">
            This secure link expires on <strong>{expires_str}</strong> and allows up to {download_max} downloads.
          </p>

          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_PAPER};border-radius:10px;">
            <tr><td style="padding:18px 20px;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:{_MUTED};">
              <strong style="color:{_INK};">Need to recover your access?</strong><br/>
              If your link has expired or you can't download, reply to this email or contact
              <a href="mailto:{support}" style="color:{_GOLD};">{support}</a> with your purchase reference
              (<strong>{order_ref}</strong>) and we'll restore your access. Keep this email as your delivery record.
            </td></tr>
          </table>

          <p style="color:#9A9A94;font-size:12px;font-family:Arial,Helvetica,sans-serif;margin:24px 0 0 0;">
            A separate Stripe payment receipt may also be sent to you. This QRU email is your product
            delivery and recovery record.
          </p>
        </td></tr>
        <tr><td style="background:{_PAPER};padding:18px 36px;border-top:1px solid #ECECE6;">
          <div style="color:#9A9A94;font-size:11px;font-family:Arial,Helvetica,sans-serif;">&copy; QRU Press&trade; &middot; Manufacture once, understand everywhere.</div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
