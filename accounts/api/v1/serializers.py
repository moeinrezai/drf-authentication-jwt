from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.models import User, Profile
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import re


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        max_length=128,
        error_messages={
            'required': 'وارد کردن رمز عبور الزامی است',
            'min_length': 'رمز عبور باید حداقل ۸ کاراکتر باشد'
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'تکرار رمز عبور الزامی است'
        }
    )
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "name", "remember_me",
            "password", "password_confirm", "access", "refresh",
            "date_joined"
        ]
        read_only_fields = ["id", "date_joined", "access", "refresh"]
        extra_kwargs = {
            'email': {
                'required': True,
                'error_messages': {
                    'required': 'وارد کردن ایمیل الزامی است'
                }
            },
            'name': {
                'required': True,
                'error_messages': {
                    'required': 'وارد کردن نام الزامی است'
                }
            },
            'remember_me': {
                'required': False,
                'default': False
            }
        }

    def validate_email(self, value):
        value = value.lower().strip()
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("فرمت ایمیل نامعتبر است")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        if value.isdigit():
            raise serializers.ValidationError("رمز عبور نمی‌تواند فقط عدد باشد")
        if value.isalpha():
            raise serializers.ValidationError("رمز عبور نمی‌تواند فقط حرف باشد")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "رمز عبور و تکرار آن مطابقت ندارند"
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=password,
            remember_me=validated_data.get('remember_me', False)
        )
        Profile.objects.get_or_create(user=user)
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        refresh = RefreshToken.for_user(instance)
        data['access'] = str(refresh.access_token)
        data['refresh'] = str(refresh)
        return data


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'وارد کردن ایمیل الزامی است',
            'invalid': 'فرمت ایمیل نامعتبر است'
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'وارد کردن رمز عبور الزامی است'
        }
    )
    remember_me = serializers.BooleanField(required=False, default=False)


    user_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    remember_me = serializers.BooleanField(read_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')
        remember_me = attrs.get('remember_me', False)

        if not email or not password:
            raise serializers.ValidationError({
                "non_field_errors": ["ایمیل و رمز عبور الزامی هستند"]
            })

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError({
                "non_field_errors": ["ایمیل یا رمز عبور اشتباه است"]
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "non_field_errors": ["حساب کاربری غیرفعال شده است"]
            })

        if user.remember_me != remember_me:
            user.remember_me = remember_me
            user.save(update_fields=['remember_me'])

        refresh = RefreshToken.for_user(user)
        return {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "remember_me": user.remember_me,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "name", "is_active",
            "date_joined", "last_login"
        ]
        read_only_fields = [
            "id", "email", "is_active", "date_joined", "last_login"
        ]
        extra_kwargs = {
            'name': {
                'error_messages': {
                    'required': 'وارد کردن نام الزامی است'
                }
            }
        }


class ProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    avatar_url = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user_email",
            "user_name",
            "bio",
            "avatar",
            "avatar_url",
            "phone_number",
            "birth_date",
            "gender",
            "gender_display",
            "website",
            "location",
            "age",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "user_email", "user_name", "avatar_url",
            "age", "gender_display", "created_at", "updated_at"
        ]
        extra_kwargs = {
            'bio': {'required': False, 'allow_blank': True},
            'phone_number': {'required': False, 'allow_blank': True},
            'birth_date': {'required': False, 'allow_null': True},
            'gender': {'required': False, 'allow_blank': True},
            'website': {'required': False, 'allow_blank': True},
            'location': {'required': False, 'allow_blank': True},
        }

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, 'url') and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_age(self, obj):
        from datetime import date
        if obj.birth_date:
            today = date.today()
            return today.year - obj.birth_date.year - (
                (today.month, today.day) < (obj.birth_date.month, obj.birth_date.day)
            )
        return None

    def validate_phone_number(self, value):
        if value:
            cleaned_value = ''.join(filter(str.isdigit, value))
            if len(cleaned_value) < 10:
                raise serializers.ValidationError("شماره تلفن باید حداقل ۱۰ رقم باشد")
            return cleaned_value
        return value

    def validate_website(self, value):
        if value and not value.startswith(('http://', 'https://')):
            return 'https://' + value
        return value

    def validate_birth_date(self, value):
        from datetime import date
        if value:
            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 1 or age > 150:
                raise serializers.ValidationError("تاریخ تولد نامعتبر است")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'وارد کردن رمز عبور فعلی الزامی است'
        }
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
        max_length=128,
        error_messages={
            'required': 'وارد کردن رمز عبور جدید الزامی است',
            'min_length': 'رمز عبور جدید باید حداقل ۸ کاراکتر باشد'
        }
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'تکرار رمز عبور جدید الزامی است'
        }
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("رمز عبور فعلی اشتباه است")
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        if value.isdigit():
            raise serializers.ValidationError("رمز عبور نمی‌تواند فقط عدد باشد")
        if value.isalpha():
            raise serializers.ValidationError("رمز عبور نمی‌تواند فقط حرف باشد")
        return value

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        old_password = attrs.get('old_password')

        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                "new_password_confirm": "رمز عبور جدید و تکرار آن مطابقت ندارند"
            })
        if old_password == new_password:
            raise serializers.ValidationError({
                "new_password": "رمز عبور جدید نباید با رمز عبور فعلی یکسان باشد"
            })
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "name", "remember_me", "is_active",
            "is_admin", "date_joined", "last_login", "profile"
        ]
        read_only_fields = [
            "id", "email", "is_admin", "date_joined", "last_login"
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "name", "remember_me", "is_active",
            "is_admin", "date_joined", "last_login", "profile"
        ]
        read_only_fields = ["id", "date_joined", "last_login"]