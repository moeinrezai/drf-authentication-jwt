from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .helpers import set_auth_cookies
from ..throttles import RefreshRateThrottle
from ..serializers import RefreshSerializer


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RefreshSerializer
    throttle_classes = [RefreshRateThrottle]

    @swagger_auto_schema(
        operation_description="تمدید توکن (چرخش خودکار)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='رفرش توکن (برای موبایل)'),
            }
        ),
        responses={
            200: openapi.Response(
                description='تمدید موفق',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: 'خطا در تمدید توکن'
        }
    )
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
