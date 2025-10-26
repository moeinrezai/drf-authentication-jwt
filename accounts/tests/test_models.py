from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Profile, GenderChoices
from django.core.exceptions import ValidationError

User = get_user_model()


class UserModelTest(TestCase):

    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'name': 'کاربر تست',
            'password': 'TestPassword123'
        }
    
    def test_create_user(self):
    
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'کاربر تست')
        self.assertTrue(user.check_password('TestPassword123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.remember_me)
        self.assertIsNotNone(user.date_joined)
    
    def test_create_superuser(self):
        """تست ایجاد سوپریوزر"""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            name='ادمین تست',
            password='AdminPassword123'
        )
        
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_admin)
        self.assertTrue(superuser.is_active)
    
    def test_user_str_representation(self):
    
        user = User.objects.create_user(**self.user_data)
        expected_str = f"{user.name} ({user.email})"
        self.assertEqual(str(user), expected_str)
    
    def test_user_email_normalization(self):
     
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            name='کاربر تست',
            password='TestPassword123'
        )
        self.assertEqual(user.email, 'test@example.com')
    
    def test_user_without_email_raises_error(self):

        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None,
                name='کاربر تست',
                password='TestPassword123'
            )
    
    def test_user_permissions(self):
    
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.has_module_perms('accounts'))
        self.assertFalse(user.has_perm('some_perm'))
        
      
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            name='ادمین',
            password='AdminPassword123'
        )
        self.assertTrue(superuser.has_perm('some_perm'))


class ProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='کاربر تست',
            password='TestPassword123'
        )
        self.profile = Profile.objects.get(user=self.user)
    
    def test_profile_creation(self):
 
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(str(self.profile), f"پروفایل {self.user.email}")
    
    def test_profile_fields(self):

        self.profile.bio = 'بیوگرافی تست'
        self.profile.phone_number = '09123456789'
        self.profile.gender = GenderChoices.MALE
        self.profile.location = 'تهران'
        self.profile.save()
        
        updated_profile = Profile.objects.get(user=self.user)
        self.assertEqual(updated_profile.bio, 'بیوگرافی تست')
        self.assertEqual(updated_profile.phone_number, '09123456789')
        self.assertEqual(updated_profile.gender, GenderChoices.MALE)
        self.assertEqual(updated_profile.location, 'تهران')
        self.assertEqual(updated_profile.get_gender_display(), 'مرد')
    

    
    def test_profile_auto_timestamps(self):

        self.assertIsNotNone(self.profile.created_at)
        self.assertIsNotNone(self.profile.updated_at)
    
    def test_profile_verbose_names(self):

        self.assertEqual(Profile._meta.verbose_name, 'پروفایل')
        self.assertEqual(Profile._meta.verbose_name_plural, 'پروفایل‌ها')