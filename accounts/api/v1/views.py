
from django.contrib.auth import get_user_model
from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.debug import sensitive_post_parameters
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework_simplejwt.authentication import JWTAuthentication

from ...models import Profile
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()





@extend_schema(
    methods=['GET'],
    description="بررسی وضعیت API و دریافت اطلاعات endpoints",
    responses={
        200: OpenApiResponse(
            description="API در حال اجراست",
            examples=[
                OpenApiExample(
                    'مثال پاسخ',
                    value={
                        "message": "✅ API در حال اجراست",
                        "endpoints": {
                            "register": "POST /api/auth/register/",
                            "login": "POST /api/auth/login/",
                            "profile": "GET /api/auth/profile/ (نیاز به توکن)",
                            "change_password": "POST /api/auth/change-password/ (نیاز به توکن)"
                        }
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_status(request):
    """
    بررسی وضعیت API
    """
    return Response({
        "message": "✅ API در حال اجراست",
        "endpoints": {
            "register": "POST /api/auth/register/",
            "login": "POST /api/auth/login/", 
            "profile": "GET /api/auth/profile/ (نیاز به توکن)",
            "change_password": "POST /api/auth/change-password/ (نیاز به توکن)",
            "logout": "POST /api/auth/logout/ (نیاز به توکن)"
        },
        "instructions": "برای تست endpointهای protected، ابتدا لاگین کنید و توکن را دریافت کنید، سپس در Swagger UI روی دکمه Authorize کلیک کنید و توکن را وارد کنید."
    })


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
        request=UserRegisterSerializer,
        responses={
            201: OpenApiResponse(
                response=UserRegisterSerializer,
                description="کاربر با موفقیت ایجاد و توکن‌ها بازگردانده شد",
                examples=[
                    OpenApiExample(
                        'مثال پاسخ موفق',
                        value={
                            "id": 1,
                            "email": "user@example.com",
                            "name": "نام کاربر",
                            "remember_me": False,
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "date_joined": "2024-01-01T12:00:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="خطای اعتبارسنجی",
                examples=[
                    OpenApiExample(
                        'مثال خطا',
                        value={
                            "email": ["این فیلد الزامی است."],
                            "password": ["رمز عبور باید حداقل ۸ کاراکتر باشد."]
                        }
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                'مثال درخواست',
                value={
                    "email": "user@example.com",
                    "name": "نام کاربر",
                    "password": "TestPassword123",
                    "password_confirm": "TestPassword123",
                    "remember_me": False
                },
                request_only=True
            )
        ]
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
                response=UserLoginSerializer,
                description="ورود موفقیت‌آمیز",
                examples=[
                    OpenApiExample(
                        'مثال پاسخ موفق',
                        value={
                            "user_id": 1,
                            "name": "نام کاربر",
                            "email": "user@example.com",
                            "is_admin": False,
                            "remember_me": False,
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="ایمیل یا رمز عبور اشتباه است",
                examples=[
                    OpenApiExample(
                        'مثال خطا',
                        value={
                            "non_field_errors": ["ایمیل یا رمز عبور اشتباه است"]
                        }
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                'مثال درخواست',
                value={
                    "email": "user@example.com",
                    "password": "TestPassword123",
                    "remember_me": False
                },
                request_only=True
            )
        ]
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
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        request={
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string', 'example': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}
            }
        },
        responses={
            204: OpenApiResponse(description="خروج موفقیت‌آمیز"),
            400: OpenApiResponse(
                description="توکن refresh نامعتبر است",
                examples=[
                    OpenApiExample(
                        'مثال خطا',
                        value={
                            "detail": "توکن refresh نامعتبر است"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="عدم احراز هویت",
                examples=[
                    OpenApiExample(
                        'مثال خطا',
                        value={
                            "detail": "Authentication credentials were not provided."
                        }
                    )
                ]
            )
        },
        auth=None  # غیرفعال کردن auth برای این endpoint خاص
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
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        return self.request.user

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="اطلاعات کاربر با موفقیت بازگردانده شد"
            ),
            401: OpenApiResponse(
                description="عدم احراز هویت",
                examples=[
                    OpenApiExample(
                        'مثال خطا',
                        value={
                            "detail": "Authentication credentials were not provided."
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=UserProfileSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="اطلاعات کاربر با موفقیت بروزرسانی شد"
            ),
            400: OpenApiResponse(description="خطای اعتبارسنجی"),
            401: OpenApiResponse(description="عدم احراز هویت")
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        request=UserProfileSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="اطلاعات کاربر با موفقیت بروزرسانی شد"
            ),
            400: OpenApiResponse(description="خطای اعتبارسنجی"),
            401: OpenApiResponse(description="عدم احراز هویت")
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    مشاهده و به‌روزرسانی پروفایل کاربر.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProfileSerializer,
                description="پروفایل کاربر با موفقیت بازگردانده شد"
            ),
            401: OpenApiResponse(description="عدم احراز هویت")
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=ProfileSerializer,
        responses={
            200: OpenApiResponse(
                response=ProfileSerializer,
                description="پروفایل کاربر با موفقیت بروزرسانی شد"
            ),
            400: OpenApiResponse(description="خطای اعتبارسنجی"),
            401: OpenApiResponse(description="عدم احراز هویت")
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        request=ProfileSerializer,
        responses={
            200: OpenApiResponse(
                response=ProfileSerializer,
                description="پروفایل کاربر با موفقیت بروزرسانی شد"
            ),
            400: OpenApiResponse(description="خطای اعتبارسنجی"),
            401: OpenApiResponse(description="عدم احراز هویت")
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class ChangePasswordView(generics.UpdateAPIView):
    """
    تغییر رمز عبور کاربر.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="رمز عبور با موفقیت تغییر کرد",
                examples=[
                    OpenApiExample(
                        'مثال پاسخ موفق',
                        value={
                            "detail": "رمز عبور با موفقیت تغییر کرد"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="خطای اعتبارسنجی"),
            401: OpenApiResponse(description="عدم احراز هویت")
        },
        examples=[
            OpenApiExample(
                'مثال درخواست',
                value={
                    "old_password": "OldPassword123",
                    "new_password": "NewPassword456",
                    "new_password_confirm": "NewPassword456"
                },
                request_only=True
            )
        ]
    )
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "رمز عبور با موفقیت تغییر کرد"},
            status=status.HTTP_200_OK
        )