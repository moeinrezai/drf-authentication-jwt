from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class MyUserManager(BaseUserManager):
    def create_user(self, email, name, remember_me=False, password=None):
        if not email:
            raise ValueError("وارد کردن ایمیل الزامی است")

        user = self.model(
            email=self.normalize_email(email),
        )
        user.name = name
        user.remember_me = remember_me
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, remember_me=False, password=None):
        user = self.create_user(
            email=email,
            name=name,
            remember_me=remember_me,
            password=password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


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

    objects = MyUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "remember_me"]

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.email

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
