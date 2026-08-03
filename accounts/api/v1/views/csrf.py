from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema


class CsrfTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @swagger_auto_schema(
        operation_description="دریافت کوکی CSRF برای مرورگرهای وب",
        responses={200: "CSRF cookie set."}
    )
    def get(self, request, *args, **kwargs):
        return Response({"detail": "CSRF cookie set."})
