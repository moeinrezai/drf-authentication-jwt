from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordConfirmSerializer,
)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @method_decorator(
        sensitive_post_parameters("old_password", "new_password", "new_password2")
    )
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @swagger_auto_schema(
        operation_description="تغییر رمز عبور کاربر جاری",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password', 'new_password2'],
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور فعلی'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور جدید'),
                'new_password2': openapi.Schema(type=openapi.TYPE_STRING, description='تکرار رمز عبور جدید'),
            }
        ),
        responses={
            200: 'رمز عبور با موفقیت تغییر کرد',
            400: 'خطای اعتبارسنجی',
            401: 'عدم احراز هویت'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "رمز عبور با موفقیت تغییر کرد. لطفاً دوباره وارد شوید."},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ForgotPasswordSerializer

    @swagger_auto_schema(
        operation_description="درخواست بازنشانی رمز عبور (ارسال ایمیل)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='ایمیل'),
            }
        ),
        responses={
            200: 'اگر ایمیل در سیستم وجود داشته باشد، لینک بازنشانی ارسال می‌شود'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "اگر این ایمیل در سیستم وجود داشته باشد لینک بازنشانی ارسال خواهد شد."}
        )


class ResetPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordConfirmSerializer

    @method_decorator(sensitive_post_parameters("new_password", "new_password2"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @swagger_auto_schema(
        operation_description="تأیید و اعمال بازنشانی رمز عبور",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['uid', 'token', 'new_password', 'new_password2'],
            properties={
                'uid': openapi.Schema(type=openapi.TYPE_STRING, description='شناسه کاربر (base64)'),
                'token': openapi.Schema(type=openapi.TYPE_STRING, description='توکن بازنشانی'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور جدید'),
                'new_password2': openapi.Schema(type=openapi.TYPE_STRING, description='تکرار رمز عبور جدید'),
            }
        ),
        responses={
            200: 'رمز عبور با موفقیت بازنشانی شد',
            400: 'خطای اعتبارسنجی'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "رمز عبور با موفقیت بازنشانی شد. اکنون می‌توانید وارد شوید."}
        )
