from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from accounts.models import Profile, GenderChoices
from accounts.api.v1.serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ProfileSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


class UserRegisterSerializerTest(TestCase):

    
    def setUp(self):
        self.valid_data = {
            'email': 'test@example.com',
            'name': 'کاربر تست',
            'password': 'TestPassword123',
            'password_confirm': 'TestPassword123',
            'remember_me': False
        }
    
    def test_valid_registration(self):
     
        serializer = UserRegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        user_data = serializer.save()
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['name'], 'کاربر تست')
        self.assertIn('access', user_data)
        self.assertIn('refresh', user_data)
        
     
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.name, 'کاربر تست')
        

        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile)
    
    def test_invalid_email_format(self):

        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        serializer = UserRegisterSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_duplicate_email(self):

        User.objects.create_user(
            email='test@example.com',
            name='کاربر اول',
            password='TestPassword123'
        )
        
  
        serializer = UserRegisterSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_password_mismatch(self):

        invalid_data = self.valid_data.copy()
        invalid_data['password_confirm'] = 'DifferentPassword123'
        
        serializer = UserRegisterSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)
    
    def test_weak_password(self):

        weak_password_data = self.valid_data.copy()
        weak_password_data['password'] = '123'
        weak_password_data['password_confirm'] = '123'
        
        serializer = UserRegisterSerializer(data=weak_password_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class UserLoginSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='کاربر تست',
            password='TestPassword123'
        )
        self.valid_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123'
        }
    
    def test_valid_login(self):

        serializer = UserLoginSerializer(
            data=self.valid_data,
            context={'request': None}
        )
        self.assertTrue(serializer.is_valid())
        
        data = serializer.validated_data
        self.assertEqual(data['user_id'], self.user.id)
        self.assertEqual(data['name'], self.user.name)
        self.assertEqual(data['email'], self.user.email)
        self.assertIn('access', data)
        self.assertIn('refresh', data)
    
    def test_invalid_credentials(self):
    
        invalid_data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        serializer = UserLoginSerializer(
            data=invalid_data,
            context={'request': None}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_nonexistent_user(self):

        invalid_data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123'
        }
        
        serializer = UserLoginSerializer(
            data=invalid_data,
            context={'request': None}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class UserProfileSerializerTest(TestCase):

    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='کاربر تست',
            password='TestPassword123'
        )
    
    def test_user_profile_serialization(self):

        serializer = UserProfileSerializer(self.user)
        
        data = serializer.data
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['name'], 'کاربر تست')
        self.assertTrue(data['is_active'])
        self.assertIn('date_joined', data)
        self.assertIn('last_login', data)
    
    def test_user_profile_update(self):

        update_data = {'name': 'نام جدید'}
        serializer = UserProfileSerializer(
            instance=self.user,
            data=update_data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.name, 'نام جدید')


class ProfileSerializerTest(TestCase):

    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='کاربر تست',
            password='TestPassword123'
        )
        self.profile = Profile.objects.get(user=self.user)
    
    def test_profile_serialization(self):

        serializer = ProfileSerializer(self.profile)
        
        data = serializer.data
        self.assertEqual(data['user_email'], 'test@example.com')
        self.assertEqual(data['user_name'], 'کاربر تست')
        self.assertIn('bio', data)
        self.assertIn('phone_number', data)

    def test_profile_update(self):
        """تست بروزرسانی پروفایل"""
        update_data = {
            'bio': 'بیوگرافی جدید',
            'phone_number': '09123456789',
            'gender': GenderChoices.MALE,
            'location': 'تهران'
        }
        
        serializer = ProfileSerializer(
            instance=self.profile,
            data=update_data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        
        self.assertEqual(updated_profile.bio, 'بیوگرافی جدید')
        self.assertEqual(updated_profile.phone_number, '09123456789')
        self.assertEqual(updated_profile.gender, GenderChoices.MALE)
        self.assertEqual(updated_profile.location, 'تهران')
    
    def test_phone_number_validation(self):

        invalid_data = {'phone_number': 'not-a-number'}
        
        serializer = ProfileSerializer(
            instance=self.profile,
            data=invalid_data,
            partial=True
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)


class ChangePasswordSerializerTest(TestCase):

    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='کاربر تست',
            password='OldPassword123'
        )
    
    def test_valid_password_change(self):
        """تست تغییر رمز عبور معتبر"""
        data = {
            'old_password': 'OldPassword123',
            'new_password': 'NewPassword456',
            'new_password_confirm': 'NewPassword456'
        }
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': type('Request', (), {'user': self.user})()}
        )
        
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
  
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword456'))
    
    def test_wrong_old_password(self):

        data = {
            'old_password': 'WrongOldPassword',
            'new_password': 'NewPassword456',
            'new_password_confirm': 'NewPassword456'
        }
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': type('Request', (), {'user': self.user})()}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)
    
    def test_password_mismatch(self):

        data = {
            'old_password': 'OldPassword123',
            'new_password': 'NewPassword456',
            'new_password_confirm': 'DifferentPassword789'
        }
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': type('Request', (), {'user': self.user})()}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password_confirm', serializer.errors)
    
    def test_same_old_new_password(self):

        data = {
            'old_password': 'OldPassword123',
            'new_password': 'OldPassword123',
            'new_password_confirm': 'OldPassword123'
        }
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': type('Request', (), {'user': self.user})()}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)