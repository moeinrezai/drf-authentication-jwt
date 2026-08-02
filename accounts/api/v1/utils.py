from django.core.mail import send_mail
from django.conf import settings
import json
from rest_framework_simplejwt.tokens import RefreshToken as RefreshTokenClass
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)


def blacklist_all_user_tokens(user):

    tokens = OutstandingToken.objects.filter(user=user)
    blacklisted_count = 0
    for token in tokens:
        _, created = BlacklistedToken.objects.get_or_create(token=token)
        if created:
            blacklisted_count += 1
    return blacklisted_count


def send_password_reset_email(user, uid, token, request=None):

    reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

    subject = _("بازنشانی رمز عبور")
    message = _(
        "درخواست بازنشانی رمز عبور برای حساب کاربری شما ارسال شده است.\n\n"
        "برای تنظیم رمز عبور جدید روی لینک زیر کلیک کنید:\n"
        "{reset_url}\n\n"
        "اگر شما این درخواست را ارسال نکرده‌اید، این ایمیل را نادیده بگیرید."
    ).format(reset_url=reset_url)

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_welcome_email(user):

    subject = _("خوش آمدید!")
    message = _(
        "سلام {name} عزیز،\n\n"
        "حساب کاربری شما با موفقیت ایجاد شد.\n"
        "از عضویت شما خوشحالیم!\n\n"
        "با احترام،\n"
        "تیم پشتیبانی"
    ).format(name=user.name)

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def blacklist_user_tokens_by_fingerprint(user_id, fp):
    tokens = OutstandingToken.objects.filter(user_id=user_id)
    blacklisted = 0
    for ot in tokens:
        try:

            token_obj = RefreshTokenClass(ot.token)
            if token_obj.payload.get("fp") == fp:
                _, created = BlacklistedToken.objects.get_or_create(token=ot)
                if created:
                    blacklisted += 1
        except Exception:
            continue
    return blacklisted
