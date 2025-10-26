from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from ...models import User, Profile



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

    class Meta:
        model = User
        fields = ["email", "name", "password", "password_confirm"]
        extra_kwargs = {
            'email': {'required': True, 'error_messages': {'required': 'وارد کردن ایمیل الزامی است'}},
            'name': {'required': True, 'error_messages': {'required': 'وارد کردن نام الزامی است'}},
        }

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        if value.isdigit() or value.isalpha():
            raise serializers.ValidationError("رمز عبور باید ترکیبی از حروف و اعداد باشد")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "رمز عبور و تکرار آن مطابقت ندارند"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        Profile.objects.get_or_create(user=user)  # اطمینان از وجود پروفایل
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        refresh = RefreshToken.for_user(instance)
        data.update({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'id': instance.id,
            'date_joined': instance.date_joined,
        })
        return data


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={'required': 'وارد کردن ایمیل الزامی است', 'invalid': 'فرمت ایمیل نامعتبر است'}
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'وارد کردن رمز عبور الزامی است'}
    )

    def validate(self, attrs):
        email = attrs['email'].lower().strip()
        password = attrs['password']

        user = authenticate(request=self.context.get('request'), username=email, password=password)
        if not user:
            raise serializers.ValidationError({"non_field_errors": ["ایمیل یا رمز عبور اشتباه است"]})
        if not user.is_active:
            raise serializers.ValidationError({"non_field_errors": ["حساب کاربری غیرفعال شده است"]})

        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        # این متد فقط برای خروجی فراخوانی می‌شود
        user = self.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "date_joined", "last_login"]
        read_only_fields = ["id", "email", "date_joined", "last_login"]


class ProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id", "user_email", "user_name", "bio", "avatar", "avatar_url",
            "phone_number", "birth_date", "website", "location", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "user_email", "user_name", "avatar_url", "created_at", "updated_at"]
        extra_kwargs = {
            'bio': {'required': False, 'allow_blank': True},
            'phone_number': {'required': False, 'allow_blank': True},
            'birth_date': {'required': False, 'allow_null': True},
            'website': {'required': False, 'allow_blank': True},
            'location': {'required': False, 'allow_blank': True},
        }

    def get_avatar_url(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url  # fallback
        return None

    def validate_website(self, value):
        if value and not value.startswith(('http://', 'https://')):
            return 'https://' + value
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

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
        if value.isdigit() or value.isalpha():
            raise serializers.ValidationError("رمز عبور باید ترکیبی از حروف و اعداد باشد")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "رمز عبور جدید و تکرار آن مطابقت ندارند"})
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": "رمز عبور جدید نباید با رمز عبور فعلی یکسان باشد"})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user