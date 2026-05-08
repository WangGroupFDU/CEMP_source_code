
import time
import smtplib
from email.mime.text import MIMEText
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

from register.tokens import activation_token

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "user@example.com"
SMTP_PASS = "<CHANGE_ME_SMTP_PASSWORD>"
MAX_RETRIES = 3
DELAY_BETWEEN_EMAILS = 3
DELAY_BETWEEN_RETRIES = 10


class Command(BaseCommand):
    help = "批量重发激活邮件给过期的 .edu 未激活用户"

    def add_arguments(self, parser):
        parser.add_argument(
            "--send", action="store_true", help="真正发送邮件(默认dry-run)"
        )
        parser.add_argument(
            "--all", action="store_true", help="发给所有过期未激活用户(不限.edu)"
        )

    def handle(self, *args, **options):
        do_send = options["send"]
        include_all = options["all"]

        threshold = timezone.now() - timedelta(days=3)
        queryset = User.objects.filter(is_active=False, date_joined__lt=threshold)

        if not include_all:
            queryset = queryset.filter(email__contains=".edu")

        users = queryset.order_by("date_joined")

        if not users.exists():
            self.stdout.write("没有需要重发的未激活用户。")
            return

        scope = "所有" if include_all else ".edu"
        self.stdout.write(f"\n找到 {users.count()} 个过期的{scope}未激活用户:\n")

        for u in users:
            days = (timezone.now() - u.date_joined).days
            self.stdout.write(f"  {u.username:20s} | {u.email:35s} | {days}天前注册")

        if not do_send:
            self.stdout.write(f"\nDRY RUN — 添加 --send 参数来执行发送。")
            return

        success, failed = 0, 0

        for i, u in enumerate(users):
            uidb64 = urlsafe_base64_encode(force_bytes(u.pk))
            token = activation_token.make_token(u)
            activation_link = (
                f"{settings.SITE_DOMAIN}/register/activate?uid={uidb64}&token={token}"
            )

            subject = "重新激活您的CEMP账号 - Reactivate Your CEMP Account"
            body = self._build_body(u.username, activation_link)

            sent = False
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
                    smtp.login(SMTP_USER, SMTP_PASS)

                    msg = MIMEText(body, "plain", "utf-8")
                    msg["Subject"] = subject
                    msg["From"] = SMTP_USER
                    msg["To"] = u.email
                    smtp.sendmail(SMTP_USER, [u.email], msg.as_string())
                    smtp.quit()

                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {u.username:20s} → {u.email}")
                    )
                    success += 1
                    sent = True
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES:
                        wait = DELAY_BETWEEN_RETRIES * attempt
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ {u.username:20s} 第{attempt}次失败: {e}，{wait}秒后重试..."
                            )
                        )
                        time.sleep(wait)
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"  ✗ {u.username:20s} → {u.email}  {MAX_RETRIES}次均失败: {e}"
                            )
                        )
                        failed += 1

            if sent and i < len(list(users)) - 1:
                time.sleep(DELAY_BETWEEN_EMAILS)

        self.stdout.write(f"\n完成: 成功 {success}, 失败 {failed}")

    def _build_body(self, username, activation_link):
        return f"""您好 {username}，

我们注意到您之前注册了CEMP（清洁能源材料平台）账号，但激活链接已过期。

我们为您重新生成了激活链接，请点击下面的链接激活您的账号：
{activation_link}

此链接将在3天后过期。

如果您没有注册CEMP账号，请忽略此邮件。

---
Hello {username},

We noticed you previously registered for a CEMP account, but your activation link has expired.

We have generated a new activation link for you:
{activation_link}

This link will expire in 3 days.

If you did not register for a CEMP account, please ignore this email.

CEMP Team
"""
