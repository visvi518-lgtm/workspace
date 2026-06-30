import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def send_email(to: str, subject: str, html: str) -> None:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP 설정이 되어 있지 않습니다. .env에 SMTP_USER, SMTP_PASSWORD를 입력해 주세요.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, to, msg.as_string())


def send_password_reset_email(to: str, reset_url: str) -> None:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
      <h2 style="color:#2563eb">MOTI 비밀번호 재설정</h2>
      <p>비밀번호 재설정을 요청하셨습니다.<br>아래 버튼을 클릭해 새 비밀번호를 설정하세요.</p>
      <a href="{reset_url}"
         style="display:inline-block;margin:24px 0;padding:12px 28px;
                background:#2563eb;color:#fff;text-decoration:none;
                border-radius:8px;font-weight:600">
        비밀번호 재설정
      </a>
      <p style="color:#6b7280;font-size:13px">
        이 링크는 1시간 후 만료됩니다.<br>
        본인이 요청하지 않았다면 이 메일을 무시하세요.
      </p>
    </div>
    """
    send_email(to, "[MOTI] 비밀번호 재설정", html)
