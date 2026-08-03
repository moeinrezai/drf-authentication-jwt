from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .helpers import set_auth_cookies
from ..serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @method_decorator(sensitive_post_parameters("password", "password2"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @swagger_auto_schema(
        operation_description="ثبت‌نام کاربر جدید",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'name', 'password', 'password2'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='ایمیل'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='نام کامل'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور'),
                'password2': openapi.Schema(type=openapi.TYPE_STRING, description='تکرار رمز عبور'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='شماره تماس (اختیاری)'),
            }
        ),
        responses={
            201: openapi.Response(
                description='ثبت‌نام موفق',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: 'خطای اعتبارسنجی'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = serializer.to_representation(user)

        if getattr(request, "device_type", None) == "web":
            response = Response(
                {"detail": "ثبت‌نام با موفقیت انجام شد."},
                status=status.HTTP_201_CREATED,
            )
            return set_auth_cookies(response, tokens["access"], tokens["refresh"])
        return Response(tokens, status=status.HTTP_201_CREATED)
