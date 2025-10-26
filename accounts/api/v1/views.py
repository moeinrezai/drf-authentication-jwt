
from django.contrib.auth import get_user_model
from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ...models import Profile
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters("password", "password_confirm", "old_password", "new_password")
)


class RegisterView(generics.CreateAPIView):
    """
    ثبت‌نام کاربر جدید و دریافت توکن‌های JWT.
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @extend_schema(
        responses={
            201: OpenApiResponse(
                description="کاربر با موفقیت ایجاد و توکن‌ها بازگردانده شد",
                examples=[
                    {
                        "email": "user@example.com",
                        "name": "نام کاربر",
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                ]
            ),
            400: OpenApiResponse(description="خطای اعتبارسنجی")
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LoginView(views.APIView):
    """
    ورود کاربر و دریافت توکن‌های JWT.
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(
                description="ورود موفقیت‌آمیز",
                examples=[
                    {
                        "user_id": 1,
                        "name": "نام کاربر",
                        "email": "user@example.com",
                        "is_admin": False,
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                ]
            ),
            400: OpenApiResponse(description="ایمیل یا رمز عبور اشتباه است")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    """
    خروج کاربر و blacklist کردن refresh token.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={"refresh": "string"},
        responses={
            204: OpenApiResponse(description="خروج موفقیت‌آمیز"),
            400: OpenApiResponse(description="توکن refresh نامعتبر است")
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "refresh الزامی است"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"detail": "توکن refresh نامعتبر است"},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    مشاهده و به‌روزرسانی اطلاعات کاربر (بدون تغییر ایمیل یا رمز عبور).
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    مشاهده و به‌روزرسانی پروفایل کاربر.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile


class ChangePasswordView(generics.UpdateAPIView):
    """
    تغییر رمز عبور کاربر.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "رمز عبور با موفقیت تغییر کرد"},
            status=status.HTTP_200_OK
        )