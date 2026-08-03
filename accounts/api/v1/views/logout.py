from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .helpers import REFRESH_COOKIE, delete_auth_cookies
from ..throttles import LogoutRateThrottle
from ..serializers import LogoutSerializer 

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [LogoutRateThrottle]
    throttle_scope = 'logout'

    @swagger_auto_schema(
        operation_description="خروج از حساب کاربری",
        request_body=LogoutSerializer,
        responses={
            200: openapi.Response(description="خروج موفقیت‌آمیز"),
            400: openapi.Response(description="درخواست نامعتبر (مثلاً رفرش توکن اشتباه)"),
            401: openapi.Response(description="عدم احراز هویت")
        }
    )
    def post(self, request, *args, **kwargs):

        serializer = LogoutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        logout_all = serializer.validated_data.get("logout_all_devices", False)

   
        refresh_token = None
        if getattr(request, "device_type", None) == "web":
            refresh_token = request.COOKIES.get(REFRESH_COOKIE)
        else:
            refresh_token = serializer.validated_data.get("refresh")

  
        if logout_all:
  
            user_tokens = OutstandingToken.objects.filter(user=request.user)
            for t in user_tokens:
    
                if not BlacklistedToken.objects.filter(token=t).exists():
                    t.blacklist()
        elif refresh_token:
     
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass


        response = Response({"detail": "خروج موفقیت‌آمیز."}, status=status.HTTP_200_OK)
        if getattr(request, "device_type", None) == "web":
            return delete_auth_cookies(response)
            
        return response