from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class MyUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("وارد کردن ایمیل الزامی است")

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(
            email=email,
            name=name,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="ایمیل",
        max_length=255,
        unique=True,
        help_text="آدرس ایمیل معتبر کاربر"
    )
    name = models.CharField(
        verbose_name="نام کامل",
        max_length=100,
        help_text="نام و نام خانوادگی کاربر"
    )
    remember_me = models.BooleanField(
        verbose_name="مرا به خاطر بسپار",
        default=False,
        help_text="در صورت فعال بودن، نشست کاربر حفظ می‌شود"
    )
    is_active = models.BooleanField(
        verbose_name="فعال",
        default=True,
        help_text="آیا حساب کاربری فعال است؟"
    )
    is_admin = models.BooleanField(
        verbose_name="مدیر",
        default=False,
        help_text="آیا کاربر دسترسی مدیریتی دارد؟"
    )
    date_joined = models.DateTimeField(
        verbose_name="تاریخ عضویت",
        auto_now_add=True
    )

    objects = MyUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]  

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.name} ({self.email})"

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class GenderChoices(models.TextChoices):
    MALE = "M", _("مرد")
    FEMALE = "F", _("زن")
    OTHER = "O", _("سایر")


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="کاربر"
    )
    bio = models.TextField(
        verbose_name="بیوگرافی",
        blank=True,
        help_text="توضیح کوتاه درباره کاربر"
    )
    avatar = models.ImageField(
        verbose_name="تصویر پروفایل",
        upload_to="avatars/",
        blank=True,
        null=True,
        help_text="آپلود تصویر پروفایل"
    )
    phone_number = models.CharField(
        verbose_name="شماره تماس",
        max_length=15,
        blank=True,
        help_text="شماره موبایل کاربر"
    )
    birth_date = models.DateField(
        verbose_name="تاریخ تولد",
        blank=True,
        null=True,
        help_text="تاریخ تولد کاربر"
    )
    gender = models.CharField(
        verbose_name="جنسیت",
        max_length=1,
        choices=GenderChoices.choices,
        blank=True,
        help_text="انتخاب جنسیت"
    )
    website = models.URLField(
        verbose_name="وب‌سایت شخصی",
        blank=True,
        help_text="آدرس وب‌سایت یا شبکه اجتماعی"
    )
    location = models.CharField(
        verbose_name="محل سکونت",
        max_length=100,
        blank=True,
        help_text="شهر یا کشور"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self):
        return f"پروفایل {self.user.email}"
