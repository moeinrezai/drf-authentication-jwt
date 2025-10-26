from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="DRF Authentication JWT API",
        default_version='v1',
        description="""
        🚀 سیستم کامل احراز هویت با Django REST Framework و JWT
        
        📌 ویژگی‌های سیستم:
        - 🔐 احراز هویت با JWT
        - 👤 مدیریت کاربران و پروفایل
        - 🛡️ دسترسی‌های امن
        - 📊 پنل مدیریت پیشرفته
        - 🎯 API کاملاً مستند
        
        🔑 دسترسی:
        - ثبت‌نام: POST /api/auth/register/
        - ورود: POST /api/auth/login/
        - خروج: POST /api/auth/logout/
        - رفرش توکن: POST /api/auth/token/refresh/
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="moeinrezaie516@gmail.com"), 
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include('accounts.urls')),
    path('swagger/output.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)