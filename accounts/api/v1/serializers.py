from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from accounts.models import Profile
from .fingerprint import generate_fingerprint

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, min_length=8,
        style={"input_type": "password"}, label=_("رمز عبور")
    )
    password2 = serializers.CharField(
        write_only=True, required=True,
        style={"input_type": "password"}, label=_("تکرار رمز عبور")
    )
    phone_number = serializers.CharField(
        required=False, allow_blank=True, max_length=15, label=_("شماره تماس")
    )

    class Meta:
        model = User
        fields = ("email", "name", "password", "password2", "phone_number")
        extra_kwargs = {
            "email": {"required": True, "label": _("ایمیل")},
            "name": {"required": True, "label": _("نام کامل")},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("این ایمیل قبلاً ثبت شده است."))
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError(
                {"password": _("رمزهای عبور با هم مطابقت ندارند.")}
            )
        return attrs

    def create(self, validated_data):
        phone_number = validated_data.pop("phone_number", None)
        user = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=validated_data["password"],
        )
        if phone_number:
            user.profile.phone_number = phone_number
            user.profile.save()
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        request = self.context.get("request")
        if request:
            fp = generate_fingerprint(request)
            refresh["fp"] = fp
            refresh.access_token["fp"] = fp
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class LoginSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].label = _("ایمیل")
        self.fields["password"].label = _("رمز عبور")

    def validate(self, attrs):
        data = super().validate(attrs)
        request = self.context.get("request")
        if request:
            refresh = RefreshToken(data["refresh"])
            fp = generate_fingerprint(request)
            refresh["fp"] = fp
            refresh.access_token["fp"] = fp
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)
        return data


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False)

    def validate(self, attrs):
        request = self.context.get("request")
        refresh_token = None
        if hasattr(request, "device_type") and request.device_type == "web":
            refresh_token = request.COOKIES.get("refresh_token")
            if not refresh_token:
                raise serializers.ValidationError({"refresh": _("کوکی رفرش پیدا نشد.")})
        else:
            refresh_token = attrs.get("refresh", "")
            if not refresh_token:
                raise serializers.ValidationError({"refresh": _("توکن رفرش الزامی است.")})

        try:
            old_refresh = RefreshToken(refresh_token)
        except Exception:
            raise serializers.ValidationError({"refresh": _("توکن رفرش نامعتبر یا منقضی شده است.")})

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    old_refresh.blacklist()
                except AttributeError:
                    pass
            new_refresh = RefreshToken.for_user(old_refresh.user)
        else:
            new_refresh = old_refresh

        if request:
            fp = generate_fingerprint(request)
            new_refresh["fp"] = fp
            new_refresh.access_token["fp"] = fp

        return {
            "access": str(new_refresh.access_token),
            "refresh": str(new_refresh),
        }

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        label=_("رمز عبور فعلی"),
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        label=_("رمز عبور جدید"),
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        label=_("تکرار رمز عبور جدید"),
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("رمز عبور فعلی اشتباه است."))
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"new_password": _("رمزهای عبور جدید مطابقت ندارند.")}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("ایمیل"))

    def validate_email(self, value):
        return value

    def save(self):
        email = self.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        from .utils import send_password_reset_email

        send_password_reset_email(user, uid, token, request=self.context.get("request"))


class ResetPasswordConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(label=_("شناسه کاربری رمزگذاری شده"))
    token = serializers.CharField(label=_("توکن بازنشانی"))
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        label=_("رمز عبور جدید"),
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        label=_("تکرار رمز عبور جدید"),
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"new_password": _("رمزهای عبور جدید مطابقت ندارند.")}
            )
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": _("شناسه کاربر نامعتبر است.")})
        if not default_token_generator.check_token(self.user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": _("توکن بازنشانی نامعتبر یا منقضی شده است.")}
            )
        return attrs

    def save(self):
        self.user.set_password(self.validated_data["new_password"])
        self.user.save(update_fields=["password"])
        return self.user


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        source="user.email", read_only=True, label=_("ایمیل")
    )
    name = serializers.CharField(
        source="user.name", read_only=True, label=_("نام کامل")
    )

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "email",
            "name",
            "bio",
            "avatar",
            "phone_number",
            "birth_date",
            "website",
            "location",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]
        extra_kwargs = {
            "bio": {"label": _("بیوگرافی")},
            "avatar": {"label": _("تصویر پروفایل")},
            "phone_number": {"label": _("شماره تماس")},
            "birth_date": {"label": _("تاریخ تولد")},
            "website": {"label": _("وب‌سایت شخصی")},
            "location": {"label": _("محل سکونت")},
        }
