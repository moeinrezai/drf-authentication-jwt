from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .helpers import REFRESH_COOKIE, delete_auth_cookies
from ..throttles import LogoutRateThrottle
from ..utils import blacklist_user_tokens_by_fingerprint


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [LogoutRateThrottle]

    @swagger_auto_schema(
        operation_description="خروج از حساب کاربری",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='رفرش توکن (برای موبایل)'),
                'logout_all_devices': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='خروج از تمام دستگاه‌های با fingerprint یکسان'
                ),
            }
        ),
        responses={
            200: 'خروج موفقیت‌آمیز',
            401: 'عدم احراز هویت'
        }
    )
    def post(self, request, *args, **kwargs):
        refresh_token = None
        if getattr(request, "device_type", None) == "web":
            refresh_token = request.COOKIES.get(REFRESH_COOKIE)
        else:
            refresh_token = request.data.get("refresh")

        logout_all = request.data.get("logout_all_devices", False)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                if logout_all:
                    fp = token.get("fp")
                    if fp:
                        blacklist_user_tokens_by_fingerprint(token["user_id"], fp)
                    else:
                        token.blacklist()
                else:
                    token.blacklist()
            except TokenError:
                pass

        if getattr(request, "device_type", None) == "web":
            response = Response({"detail": "خروج موفقیت‌آمیز."})
            return delete_auth_cookies(response)
        return Response({"detail": "خروج موفقیت‌آمیز."})