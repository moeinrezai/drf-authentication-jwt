from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Profile
from django.core.exceptions import ValidationError

User = get_user_model()


class UserModelTest(TestCase):
    """
    تست مدل User
    """

    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "name": "کاربر تست",
            "password": "TestPassword123",
        }

    def test_create_user(self):
        """تست ایجاد کاربر معمولی"""
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "کاربر تست")
        self.assertTrue(user.check_password("TestPassword123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
        self.assertIsNotNone(user.date_joined)

    def test_create_superuser(self):
        """تست ایجاد سوپریوزر"""
        superuser = User.objects.create_superuser(
            email="admin@example.com", name="ادمین تست", password="AdminPassword123"
        )

        self.assertEqual(superuser.email, "admin@example.com")
        self.assertTrue(superuser.is_admin)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)

    def test_user_str_representation(self):
        """تست نمایش رشته کاربر"""
        user = User.objects.create_user(**self.user_data)
        expected_str = f"{user.name} ({user.email})"
        self.assertEqual(str(user), expected_str)

    def test_user_without_email_raises_error(self):
        """تست ایجاد کاربر بدون ایمیل"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None, name="کاربر تست", password="TestPassword123"
            )

    def test_user_permissions(self):
        """تست دسترسی‌های کاربر"""
        # تست کاربر معمولی
        user = User.objects.create_user(**self.user_data)

        # کاربر معمولی نباید دسترسی ادمین داشته باشد
        self.assertFalse(user.has_module_perms("accounts"))
        self.assertFalse(user.has_perm("some_permission"))

        # تست سوپریوزر
        superuser = User.objects.create_superuser(
            email="admin@example.com", name="ادمین", password="AdminPassword123"
        )
        self.assertTrue(superuser.has_module_perms("accounts"))
        self.assertTrue(superuser.has_perm("some_permission"))

    def test_user_admin_permissions(self):
        """تست دسترسی‌های کاربر ادمین"""
        admin_user = User.objects.create_user(
            email="admin@example.com",
            name="ادمین تست",
            password="AdminPassword123",
            is_admin=True,
        )

        self.assertTrue(admin_user.has_module_perms("accounts"))
        self.assertTrue(admin_user.has_perm("some_permission"))

    def test_user_staff_property(self):
        """تست property is_staff"""
        normal_user = User.objects.create_user(**self.user_data)
        self.assertFalse(normal_user.is_staff)

        admin_user = User.objects.create_user(
            email="admin@example.com",
            name="ادمین تست",
            password="AdminPassword123",
            is_admin=True,
        )
        self.assertTrue(admin_user.is_staff)


class ProfileModelTest(TestCase):
    """
    تست مدل Profile
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", name="کاربر تست", password="TestPassword123"
        )
        # ایجاد پروفایل به صورت دستی
        self.profile, created = Profile.objects.get_or_create(user=self.user)

    def test_profile_creation(self):
        """تست ایجاد پروفایل"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(str(self.profile), f"پروفایل {self.user.email}")

    def test_profile_fields(self):
        """تست فیلدهای پروفایل"""
        self.profile.bio = "بیوگرافی تست"
        self.profile.phone_number = "09123456789"
        self.profile.location = "تهران"
        self.profile.save()

        updated_profile = Profile.objects.get(user=self.user)
        self.assertEqual(updated_profile.bio, "بیوگرافی تست")
        self.assertEqual(updated_profile.phone_number, "09123456789")
        self.assertEqual(updated_profile.location, "تهران")

    def test_profile_auto_timestamps(self):
        """تست زمان‌های خودکار"""
        self.assertIsNotNone(self.profile.created_at)
        self.assertIsNotNone(self.profile.updated_at)

    def test_profile_verbose_names(self):
        """تست نام‌های نمایشی"""
        self.assertEqual(Profile._meta.verbose_name, "پروفایل")
        self.assertEqual(Profile._meta.verbose_name_plural, "پروفایل‌ها")
