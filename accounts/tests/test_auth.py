from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


class BaseAPITest(APITestCase):
    def authenticate(self, user=None):
        if user is None:
            user = self.user
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return refresh


class AuthenticationAPITest(BaseAPITest):
    def setUp(self):
        self.register_url = reverse("accounts_v1:register")
        self.login_url = reverse("accounts_v1:login")
        self.logout_url = reverse("accounts_v1:logout")
        self.refresh_url = reverse("accounts_v1:refresh")
        self.csrf_url = reverse("accounts_v1:csrf")
        self.change_password_url = reverse("accounts_v1:change_password")
        self.profile_url = reverse("accounts_v1:profile")

        self.register_data = {
            "email": "test@example.com",
            "name": "کاربر تست",
            "password": "TestPass123",
            "password2": "TestPass123",
        }
        self.login_data = {"email": "test@example.com", "password": "TestPass123"}
        self.user = User.objects.create_user(**self.register_data)

        self.mobile_ua = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
        self.web_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


    def test_csrf_endpoint_web(self):
        response = self.client.get(self.csrf_url, HTTP_USER_AGENT=self.web_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("csrftoken", response.cookies)

    # ---------- Register ----------
    def test_register_valid_mobile(self):
        data = self.register_data.copy()
        data["email"] = "new@example.com"
        response = self.client.post(
            self.register_url, data, format="json", HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_register_valid_web(self):
        data = self.register_data.copy()
        data["email"] = "web@example.com"
        # ابتدا CSRF بگیریم
        csrf_resp = self.client.get(self.csrf_url, HTTP_USER_AGENT=self.web_ua)
        csrf_token = csrf_resp.cookies["csrftoken"].value
        response = self.client.post(
            self.register_url,
            data,
            format="json",
            HTTP_USER_AGENT=self.web_ua,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertIn("detail", response.data)

    def test_register_duplicate_email(self):
        response = self.client.post(
            self.register_url,
            self.register_data,
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_password_mismatch(self):
        data = self.register_data.copy()
        data["email"] = "bad@example.com"
        data["password2"] = "Different"
        response = self.client.post(
            self.register_url, data, format="json", HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


    def test_login_valid_mobile(self):
        response = self.client.post(
            self.login_url,
            self.login_data,
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_valid_web(self):
        csrf_resp = self.client.get(self.csrf_url, HTTP_USER_AGENT=self.web_ua)
        csrf_token = csrf_resp.cookies["csrftoken"].value
        response = self.client.post(
            self.login_url,
            self.login_data,
            format="json",
            HTTP_USER_AGENT=self.web_ua,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {"email": "test@example.com", "password": "wrong"},
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_logout_mobile_blacklists_token(self):
        refresh = self.authenticate(self.user)
        response = self.client.post(
            self.logout_url,
            {"refresh": str(refresh)},
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=refresh.payload["jti"]).exists()
        )

    def test_logout_web_clears_cookies(self):
      
        csrf_resp = self.client.get(self.csrf_url, HTTP_USER_AGENT=self.web_ua)
        csrf_token = csrf_resp.cookies["csrftoken"].value
        login_resp = self.client.post(
            self.login_url,
            self.login_data,
            format="json",
            HTTP_USER_AGENT=self.web_ua,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
    
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.logout_url, {}, HTTP_USER_AGENT=self.web_ua,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for cookie_name in ["access_token", "refresh_token"]:
            cookie = response.cookies.get(cookie_name)
            self.assertIsNotNone(cookie)
            self.assertEqual(cookie.value, "")


    def test_refresh_rotates_and_blacklists(self):
        refresh = self.authenticate(self.user)
        old_jti = refresh.payload["jti"]
        response = self.client.post(
            self.refresh_url,
            {"refresh": str(refresh)},
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=old_jti).exists())
        new_refresh = response.data["refresh"]
        self.assertTrue(RefreshToken(new_refresh).check_blacklist() is None)

    def test_refresh_with_blacklisted_fails(self):
        refresh = self.authenticate(self.user)
        refresh.blacklist()
        response = self.client.post(
            self.refresh_url,
            {"refresh": str(refresh)},
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

  
    def test_change_password_success(self):
        refresh = self.authenticate(self.user)
        response = self.client.post(
            self.change_password_url,
            {
                "old_password": "TestPass123",
                "new_password": "NewPass456",
                "new_password2": "NewPass456",
            },
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456"))
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=refresh.payload["jti"]).exists()
        )

    def test_change_password_wrong_old(self):
        self.authenticate(self.user)
        response = self.client.post(
            self.change_password_url,
            {
                "old_password": "WrongOld",
                "new_password": "NewPass456",
                "new_password2": "NewPass456",
            },
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)


    def test_get_profile(self):
        self.authenticate(self.user)
        response = self.client.get(self.profile_url, HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_update_profile(self):
        self.authenticate(self.user)
        response = self.client.patch(
            self.profile_url,
            {"bio": "درباره من", "phone_number": "09123456789"},
            format="json",
            HTTP_USER_AGENT=self.mobile_ua,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "درباره من")

    def test_profile_unauthorized(self):
        response = self.client.get(self.profile_url, HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)