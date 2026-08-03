from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.contrib.auth import get_user_model
from time import sleep

User = get_user_model()


class SecurityFeaturesTest(APITestCase):
    def setUp(self):
        self.login_url = reverse("accounts_v1:login")
        self.profile_url = reverse("accounts_v1:profile")
        self.logout_url = reverse("accounts_v1:logout")
        self.register_url = reverse("accounts_v1:register")
        self.refresh_url = reverse("accounts_v1:refresh")

        self.user_data = {
            "email": "secuser@example.com",
            "name": "Security User",
            "password": "TestPass123",
            "password2": "TestPass123",
        }
        self.login_data = {"email": "secuser@example.com", "password": "TestPass123"}
        self.user = User.objects.create_user(**self.user_data)

        self.mobile_ua = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
        self.iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"

    def _get_tokens(self):
        resp = self.client.post(
            self.login_url, self.login_data,
            format="json", HTTP_USER_AGENT=self.mobile_ua
        )
        return resp.json()["access"], resp.json()["refresh"]

    
    def test_fingerprint_same_device_access(self):
        access, _ = self._get_tokens()
        resp = self.client.get(
            self.profile_url,
            HTTP_AUTHORIZATION=f"Bearer {access}",
            HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


    def test_fingerprint_different_device_blocked(self):
        access, _ = self._get_tokens()
        resp = self.client.get(
            self.profile_url,
            HTTP_AUTHORIZATION=f"Bearer {access}",
            HTTP_USER_AGENT=self.iphone_ua
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_old_token_without_fp_works(self):
     
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)
        resp = self.client.get(
            self.profile_url,
            HTTP_AUTHORIZATION=f"Bearer {access}",
            HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @override_settings(REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'accounts.api.v1.authentication.CookieOrHeaderJWTAuthentication',
        ),
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '10/minute',
            'user': '20/minute',
            'login': '5/min',
            'refresh': '10/min',
            'logout': '10/min',
        },
    })
    def test_login_rate_limiting(self):
        for i in range(5):
            resp = self.client.post(
                self.login_url, self.login_data,
                format="json", HTTP_USER_AGENT=self.mobile_ua
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.client.post(
            self.login_url, self.login_data,
            format="json", HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

   
    def test_logout_blacklists_refresh(self):
        access, refresh = self._get_tokens()
        resp = self.client.post(
            self.logout_url,
            {"refresh": refresh},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
            HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(
            self.refresh_url,
            {"refresh": refresh},
            format="json",
            HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_all_devices_by_fingerprint(self):
       
        _, refresh1 = self._get_tokens()
       
        access2, refresh2 = self._get_tokens()
     
        resp = self.client.post(
            self.logout_url,
            {"refresh": refresh2, "logout_all_devices": True},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {access2}",
            HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
      
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=RefreshToken(refresh1).payload["jti"]).exists())
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=RefreshToken(refresh2).payload["jti"]).exists())

    def test_change_password_invalidates_all_tokens(self):
        access, refresh = self._get_tokens()

        resp = self.client.post(
            reverse("accounts_v1:change_password"),
            {
                "old_password": "TestPass123",
                "new_password": "NewPass456",
                "new_password2": "NewPass456",
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
            HTTP_USER_AGENT=self.mobile_ua
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
     
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=RefreshToken(refresh).payload["jti"]).exists())