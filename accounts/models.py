from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class MyUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    instead of usernames.
    """

    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError(_("وارد کردن ایمیل الزامی است"))
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_admin") is not True:
            raise ValueError(_("Superuser must have is_admin=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):


    email = models.EmailField(_("ایمیل"), max_length=255, unique=True)
    name = models.CharField(_("نام کامل"), max_length=100)
    is_active = models.BooleanField(_("فعال"), default=True)
    is_admin = models.BooleanField(_("مدیر"), default=False)
    date_joined = models.DateTimeField(_("تاریخ عضویت"), default=timezone.now)

    objects = MyUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.name} ({self.email})"
    

    def has_perm(self, perm, obj=None):
        """
        بررسی دسترسی خاص
        """
        if self.is_admin or self.is_superuser:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        """
        بررسی دسترسی به ماژول
        """
        if self.is_admin or self.is_superuser:
            return True
        return super().has_module_perms(app_label)

    @property
    def is_staff(self):
        """Required by Django admin to determine if user can access admin site."""
        return self.is_admin


class Profile(models.Model):
    """
    Extended user profile with additional personal information.
    """

    # اعتبارسنجی اختیاری برای شماره تلفن ایرانی
    iranian_phone_validator = RegexValidator(
        regex=r"^09[0-9]{9}$",
        message=_("شماره تلفن باید یک شماره موبایل معتبر ایرانی باشد (مثلاً 09123456789).")
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("کاربر")
    )
    bio = models.TextField(_("بیوگرافی"), blank=True)
    avatar = models.ImageField(_("تصویر پروفایل"), upload_to="avatars/", blank=True)
    phone_number = models.CharField(
        _("شماره تماس"),
        max_length=15,
        blank=True,
        validators=[iranian_phone_validator]
    )
    birth_date = models.DateField(_("تاریخ تولد"), blank=True, null=True)
    website = models.URLField(_("وب‌سایت شخصی"), blank=True)
    location = models.CharField(_("محل سکونت"), max_length=100, blank=True)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("آخرین بروزرسانی"), auto_now=True)

    class Meta:
        verbose_name = _("پروفایل")
        verbose_name_plural = _("پروفایل‌ها")

    def __str__(self):
        return _("پروفایل {email}").format(email=self.user.email)