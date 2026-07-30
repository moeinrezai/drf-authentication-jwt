# accounts/tests/test_serializers.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Profile
from accounts.api.v1.serializers import (
    RegisterSerializer,
    LoginSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
    RefreshSerializer,
)

User = get_user_model()


class RegisterSerializerTest(TestCase):

    def setUp(self):
        self.valid_data = {
            "email": "test@example.com",
            "name": "کاربر تست",
            "password": "TestPassword123",
            "password2": "TestPassword123",
            "phone_number": "09123456789",
        }

    def test_valid_registration(self):
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "کاربر تست")
        # خروجی نهایی توکن‌ها را می‌دهد
        output = serializer.to_representation(user)
        self.assertIn("access", output)
        self.assertIn("refresh", output)
        # پروفایل خودکار ایجاد شده باشد
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_invalid_email_format(self):
        data = self.valid_data.copy()
        data["email"] = "invalid-email"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_duplicate_email(self):
        User.objects.create_user(**self.valid_data)
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_password_mismatch(self):
        data = self.valid_data.copy()
        data["password2"] = "DifferentPass123"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)  # خطا در فیلد password

    def test_weak_password(self):
        data = self.valid_data.copy()
        data["password"] = "123"
        data["password2"] = "123"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


class LoginSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", name="کاربر تست", password="TestPassword123"
        )
        self.valid_data = {"email": "test@example.com", "password": "TestPassword123"}

    def test_valid_login(self):
        serializer = LoginSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        # خروجی استاندارد: فقط access و refresh
        tokens = serializer.validated_data
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    def test_invalid_credentials(self):
        data = {"email": "test@example.com", "password": "WrongPass"}
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_nonexistent_user(self):
        data = {"email": "unknown@example.com", "password": "pass"}
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)


class ProfileSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", name="کاربر تست", password="TestPassword123"
        )
        self.profile = Profile.objects.get(user=self.user)

    def test_profile_serialization(self):
        serializer = ProfileSerializer(self.profile)
        data = serializer.data
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["name"], "کاربر تست")
        self.assertIn("bio", data)
        self.assertIn("phone_number", data)

    def test_profile_update(self):
        data = {
            "bio": "بیوگرافی جدید",
            "phone_number": "09123456789",
            "location": "تهران",
        }
        serializer = ProfileSerializer(instance=self.profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.bio, "بیوگرافی جدید")
        self.assertEqual(updated.phone_number, "09123456789")
        self.assertEqual(updated.location, "تهران")

    def test_phone_number_validation(self):
        data = {"phone_number": "not-a-number"}
        serializer = ProfileSerializer(instance=self.profile, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)


class ChangePasswordSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", name="کاربر تست", password="OldPassword123"
        )

    def test_valid_password_change(self):
        data = {
            "old_password": "OldPassword123",
            "new_password": "NewPassword456",
            "new_password2": "NewPassword456",
        }
        # ایجاد یک request مصنوعی
        request = type("Request", (), {"user": self.user})()
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword456"))

    def test_wrong_old_password(self):
        data = {
            "old_password": "WrongOldPassword",
            "new_password": "NewPassword456",
            "new_password2": "NewPassword456",
        }
        request = type("Request", (), {"user": self.user})()
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_password", serializer.errors)

    def test_password_mismatch(self):
        data = {
            "old_password": "OldPassword123",
            "new_password": "NewPassword456",
            "new_password2": "DifferentPass",
        }
        request = type("Request", (), {"user": self.user})()
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)

    def test_weak_new_password(self):
        data = {
            "old_password": "OldPassword123",
            "new_password": "123",
            "new_password2": "123",
        }
        request = type("Request", (), {"user": self.user})()
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)
