
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


class BaseAPITest(APITestCase):
    """کلاس پایه برای تنظیمات مشترک تست‌ها"""

    def authenticate(self, user=None):
        """احراز هویت یک کاربر و افزودن توکن به هدر"""
        if user is None:
            user = self.user
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return refresh


class AuthenticationAPITest(BaseAPITest):

    def setUp(self):
        # URL names (app_name = 'accounts_v1')
        self.register_url = reverse('accounts_v1:register')
        self.login_url = reverse('accounts_v1:login')
        self.logout_url = reverse('accounts_v1:logout')
        self.refresh_url = reverse('accounts_v1:refresh')
        self.csrf_url = reverse('accounts_v1:csrf')
        self.change_password_url = reverse('accounts_v1:change_password')
        self.profile_url = reverse('accounts_v1:profile')

        # داده‌های معتبر برای ثبت‌نام
        self.register_data = {
            'email': 'test@example.com',
            'name': 'کاربر تست',
            'password': 'TestPass123',
            'password2': 'TestPass123'
        }

        # داده‌های ورود
        self.login_data = {
            'email': 'test@example.com',
            'password': 'TestPass123'
        }

        # ایجاد یک کاربر برای تست‌های ورود / logout و غیره
        self.user = User.objects.create_user(**self.register_data)

        # هدر پیش‌فرض موبایل (برای ساده‌سازی تست‌ها و غیرفعال شدن CSRF)
        self.mobile_ua = 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36'
        self.web_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    # ---------- CSRF ----------
    def test_csrf_endpoint_web(self):
        """درخواست کوکی CSRF از مرورگر وب"""
        response = self.client.get(self.csrf_url, HTTP_USER_AGENT=self.web_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrftoken', response.cookies)

    # ---------- Register ----------
    def test_register_valid_mobile(self):
        """ثبت‌نام درست از طریق موبایل (توکن‌ها در JSON)"""
        data = self.register_data.copy()
        data['email'] = 'new@example.com'
        response = self.client.post(self.register_url, data, format='json',
                                    HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_register_valid_web(self):
        """ثبت‌نام درست از وب (توکن‌ها در کوکی)"""
        data = self.register_data.copy()
        data['email'] = 'web@example.com'
        response = self.client.post(self.register_url, data, format='json',
                                    HTTP_USER_AGENT=self.web_ua)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # بررسی وجود کوکی‌ها
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        # بدنه پاسخ فقط پیغام دارد
        self.assertIn('detail', response.data)

    def test_register_duplicate_email(self):
        """ایمیل تکراری – باید ۴۰۰ برگرداند"""
        response = self.client.post(self.register_url, self.register_data, format='json',
                                    HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_password_mismatch(self):
        """عدم تطابق رمزها"""
        data = self.register_data.copy()
        data['email'] = 'bad@example.com'
        data['password2'] = 'Different'
        response = self.client.post(self.register_url, data, format='json',
                                    HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    # ---------- Login ----------
    def test_login_valid_mobile(self):
        """ورود موفق از موبایل (JSON بازگشتی)"""
        response = self.client.post(self.login_url, self.login_data, format='json',
                                    HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_valid_web(self):
        """ورود موفق از وب (کوکی)"""
        response = self.client.post(self.login_url, self.login_data, format='json',
                                    HTTP_USER_AGENT=self.web_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_invalid_credentials(self):
        """ورود ناموفق – ۴۰۰"""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrong'
        }, format='json', HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- Logout ----------
    def test_logout_mobile_blacklists_token(self):
        """خروج از موبایل – توکن رفرش بلاک‌لیست می‌شود"""
        refresh = self.authenticate(self.user)  # لاگین و ست کردن هدر
        response = self.client.post(self.logout_url, {'refresh': str(refresh)},
                                    format='json', HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # بررسی بلاک‌لیست شدن توکن
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=refresh['jti']).exists())

    def test_logout_web_clears_cookies(self):
        """خروج از وب – کوکی‌ها پاک می‌شوند"""
        # ابتدا لاگین وب تا کوکی‌ها ست شوند
        login_response = self.client.post(self.login_url, self.login_data,
                                          format='json', HTTP_USER_AGENT=self.web_ua)
        # اکنون کوکی‌ها در client هستند
        response = self.client.post(self.logout_url, {},
                                    HTTP_USER_AGENT=self.web_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # کوکی‌ها باید خالی شده باشند
        for cookie_name in ['access_token', 'refresh_token']:
            cookie = response.cookies.get(cookie_name)
            self.assertIsNotNone(cookie)
            self.assertEqual(cookie.value, '')

    # ---------- Refresh ----------
    def test_refresh_rotates_and_blacklists(self):
        """رفرش توکن: چرخش انجام شده و توکن قبلی بلاک‌لیست می‌شود"""
        refresh = self.authenticate(self.user)
        old_jti = refresh.payload['jti']
        response = self.client.post(self.refresh_url, {'refresh': str(refresh)},
                                    format='json', HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # توکن قدیمی بلاک‌لیست شده باشد
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=old_jti).exists())
        # توکن جدید معتبر باشد
        new_refresh = response.data['refresh']
        self.assertTrue(RefreshToken(new_refresh).check_blacklist() is None)

    def test_refresh_with_blacklisted_fails(self):
        """تلاش برای رفرش با توکن بلاک‌لیست شده – باید ۴۰۰ دهد"""
        refresh = self.authenticate(self.user)
        refresh.blacklist()
        response = self.client.post(self.refresh_url, {'refresh': str(refresh)},
                                    format='json', HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- Change Password ----------
    def test_change_password_success(self):
        """تغییر رمز عبور موفق – و باطل شدن همه توکن‌های قبلی"""
        refresh = self.authenticate(self.user)
        # تغییر رمز
        response = self.client.post(self.change_password_url, {
            'old_password': 'TestPass123',
            'new_password': 'NewPass456',
            'new_password2': 'NewPass456'
        }, format='json', HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # چک کنیم رمز تغییر کرده
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass456'))

        # توکن رفرش قدیمی بلاک‌لیست شده باشد
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=refresh.payload['jti']).exists())

    def test_change_password_wrong_old(self):
        """تغییر رمز با رمز قدیمی اشتباه"""
        self.authenticate(self.user)
        response = self.client.post(self.change_password_url, {
            'old_password': 'WrongOld',
            'new_password': 'NewPass456',
            'new_password2': 'NewPass456'
        }, format='json', HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    # ---------- Profile ----------
    def test_get_profile(self):
        """دریافت پروفایل کاربر"""
        self.authenticate(self.user)
        response = self.client.get(self.profile_url, HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_update_profile(self):
        """به‌روزرسانی پروفایل"""
        self.authenticate(self.user)
        response = self.client.patch(self.profile_url, {
            'bio': 'درباره من',
            'phone_number': '09123456789'
        }, format='json', HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'درباره من')

    def test_profile_unauthorized(self):
        """دسترسی بدون احراز هویت"""
        response = self.client.get(self.profile_url, HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionsAPITest(BaseAPITest):

    def setUp(self):
        # ایجاد کاربران با گروه‌های مختلف
        self.admin_user = User.objects.create_user(
            email='admin@test.com', name='ادمین', password='pass'
        )
        # فرض می‌کنیم گروه 'admin' را در migrate یا fixture ساخته‌اید
        # اینجا باید گروه وجود داشته باشد. برای سادگی می‌توانید در setUpTestData یا در ابتدای کلاس بسازید.
        from django.contrib.auth.models import Group
        admin_group, _ = Group.objects.get_or_create(name='admin')
        self.admin_user.groups.add(admin_group)

        self.normal_user = User.objects.create_user(
            email='normal@test.com', name='معمولی', password='pass'
        )

        self.profile_url = reverse('accounts_v1:profile')

    def test_admin_can_access(self):
      
        self.authenticate(self.admin_user)
        response = self.client.get(self.profile_url, HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_normal_user_can_access(self):
        """کاربر معمولی هم می‌تواند پروفایل خود را ببیند"""
        self.authenticate(self.normal_user)
        response = self.client.get(self.profile_url, HTTP_USER_AGENT=self.mobile_ua)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

