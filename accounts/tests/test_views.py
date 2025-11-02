from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


class AuthenticationViewsTest(APITestCase):
    
    def setUp(self):
        # استفاده از reverse() برای جلوگیری از خطاهای مسیر و افزایش ایمنی
        self.register_url = reverse('accounts_api_v1:register')
        self.login_url = reverse('accounts_api_v1:login')
        self.logout_url = reverse('accounts_api_v1:logout')
        self.change_password_url = reverse('accounts_api_v1:change-password')
        self.api_status_url = reverse('accounts_api_v1:api-status')
        
        self.user_data = {
            'email': 'test@example.com',
            'name': 'کاربر تست',
            'password': 'TestPassword123',
            'password_confirm': 'TestPassword123',
            'remember_me': False
        }
        
        self.login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123'
        }
    
    def test_user_registration(self):
        """تست ثبت‌نام کاربر"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_user_registration_invalid_data(self):
        """تست ثبت‌نام با داده نامعتبر"""
        invalid_data = self.user_data.copy()
        invalid_data['password_confirm'] = 'DifferentPassword'
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login(self):
        """تست ورود کاربر"""
        User.objects.create_user(**{
            'email': 'test@example.com',
            'name': 'کاربر تست',
            'password': 'TestPassword123'
        })
        response = self.client.post(self.login_url, self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_login_invalid_credentials(self):
        """تست ورود با اطلاعات نامعتبر"""
        response = self.client.post(self.login_url, self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_logout(self):
        """تست خروج کاربر"""
        user = User.objects.create_user(**{
            'email': 'test@example.com',
            'name': 'کاربر تست',
            'password': 'TestPassword123'
        })
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_data = {'refresh': str(refresh)}
        response = self.client.post(self.logout_url, logout_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_urls_are_correct(self):
        """تست تطابق نام‌های URL با مسیرهای واقعی — ایمن‌سازی اضافی"""
        urls = [
            ('register', '/api/auth/register/'),
            ('login', '/api/auth/login/'),
            ('logout', '/api/auth/logout/'),
            ('change-password', '/api/auth/change-password/'),
            ('api-status', '/api/auth/'),
        ]
        
        for name, expected_url in urls:
            with self.subTest(name=name):
                url = reverse(f'accounts_api_v1:{name}')
                self.assertEqual(url, expected_url)


class ProfileViewsTest(APITestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='کاربر تست',
            password='TestPassword123'
        )
        self.profile = Profile.objects.get(user=self.user)
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # استفاده از reverse() برای تمام مسیرها — ایمن و قابل انتقال
        self.user_profile_url = reverse('accounts_api_v1:user-profile')
        self.profile_detail_url = reverse('accounts_api_v1:profile-detail')
        self.change_password_url = reverse('accounts_api_v1:change-password')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_user_profile(self):
        """تست دریافت اطلاعات کاربر"""
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_update_user_profile(self):
        """تست بروزرسانی اطلاعات کاربر"""
        update_data = {'name': 'نام جدید کاربر'}
        response = self.client.patch(self.user_profile_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_profile_detail(self):
        """تست دریافت اطلاعات پروفایل"""
        response = self.client.get(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_update_profile_detail(self):
        """تست بروزرسانی اطلاعات پروفایل"""
        update_data = {
            'bio': 'بیوگرافی جدید',
            'phone_number': '09123456789',
            'location': 'مشهد'
        }
        response = self.client.patch(self.profile_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_change_password(self):
        """تست تغییر رمز عبور"""
        change_password_data = {
            'old_password': 'TestPassword123',
            'new_password': 'NewPassword456',
            'new_password_confirm': 'NewPassword456'
        }
        response = self.client.post(self.change_password_url, change_password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_change_password_wrong_old_password(self):
        """تست تغییر رمز عبور با رمز قدیمی اشتباه"""
        change_password_data = {
            'old_password': 'WrongPassword',
            'new_password': 'NewPassword456',
            'new_password_confirm': 'NewPassword456'
        }
        response = self.client.post(self.change_password_url, change_password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthorized_access(self):
        """تست دسترسی بدون احراز هویت"""
        self.client.credentials()  # حذف توکن
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ApiStatusViewTest(APITestCase):
    
    def test_api_status(self):
        """تست وضعیت API"""
        url = reverse('accounts_api_v1:api-status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)