from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .throttles import LoginRateThrottle, RefreshRateThrottle, LogoutRateThrottle
from .utils import blacklist_user_tokens_by_fingerprint
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    RefreshSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordConfirmSerializer,
    ProfileSerializer,
)

jwt_settings = getattr(settings, "SIMPLE_JWT", {})
ACCESS_COOKIE = jwt_settings.get("AUTH_COOKIE", "access_token")
REFRESH_COOKIE = jwt_settings.get("AUTH_COOKIE_REFRESH", "refresh_token")
COOKIE_SAMESITE = jwt_settings.get("AUTH_COOKIE_SAMESITE", "Lax")
COOKIE_HTTPONLY = jwt_settings.get("AUTH_COOKIE_HTTP_ONLY", True)
COOKIE_SECURE = jwt_settings.get("AUTH_COOKIE_SECURE", not settings.DEBUG)
COOKIE_PATH = jwt_settings.get("AUTH_COOKIE_PATH", "/")


def set_auth_cookies(response, access_token, refresh_token):
    response.set_cookie(
        key=ACCESS_COOKIE, value=access_token,
        httponly=COOKIE_HTTPONLY, secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE, path=COOKIE_PATH,
    )
    response.set_cookie(
        key=REFRESH_COOKIE, value=refresh_token,
        httponly=COOKIE_HTTPONLY, secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE, path=COOKIE_PATH,
    )
    return response


def delete_auth_cookies(response):
    response.delete_cookie(ACCESS_COOKIE, path=COOKIE_PATH)
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
    return response


class CsrfTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return Response({"detail": "CSRF cookie set."})


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @method_decorator(sensitive_post_parameters("password", "password2"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

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


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    throttle_classes = [LoginRateThrottle]

    @method_decorator(sensitive_post_parameters("password"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if getattr(request, "device_type", None) == "web":
            response = Response({"detail": "ورود موفقیت‌آمیز."})
            return set_auth_cookies(response, data["access"], data["refresh"])
        return Response(data)


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RefreshSerializer
    throttle_classes = [RefreshRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data

        if getattr(request, "device_type", None) == "web":
            response = Response({"detail": "توکن با موفقیت تمدید شد."})
            return set_auth_cookies(response, tokens["access"], tokens["refresh"])
        return Response(tokens)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [LogoutRateThrottle]   # اصلاح شد

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


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @method_decorator(
        sensitive_post_parameters("old_password", "new_password", "new_password2")
    )
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

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

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "رمز عبور با موفقیت بازنشانی شد. اکنون می‌توانید وارد شوید."}
        )


class ProfileView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile