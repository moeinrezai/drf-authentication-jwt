from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ...models import User, Profile
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
    UserDetailSerializer
)


class RegisterView(APIView):
    """
    ویو برای ثبت‌نام کاربر جدید
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="ثبت‌نام کاربر جدید",
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response('ثبت‌نام موفق', UserRegisterSerializer),
            400: 'اطلاعات وارد شده معتبر نیست'
        }
    )
    @transaction.atomic
    def post(self, request):
        """
        ثبت‌نام کاربر جدید
        """
        try:
            serializer = UserRegisterSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    "status": "error",
                    "message": "اطلاعات وارد شده معتبر نیست",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
    
            user_data = serializer.save()
            
            return Response({
                "status": "success",
                "message": "ثبت‌نام با موفقیت انجام شد",
                "data": user_data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                "status": "error",
                "message": "خطا در اعتبارسنجی داده‌ها",
                "errors": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطای سرور در ثبت‌نام",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    """
    ویو برای ورود کاربر
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="ورود کاربر",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response('ورود موفق', UserLoginSerializer),
            400: 'اطلاعات وارد شده معتبر نیست',
            404: 'کاربر یافت نشد'
        }
    )
    def post(self, request):
        """
        ورود کاربر
        """
        try:
            serializer = UserLoginSerializer(
                data=request.data, 
                context={'request': request}
            )
            
            if not serializer.is_valid():
                return Response({
                    "status": "error",
                    "message": "اطلاعات وارد شده معتبر نیست",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # بروزرسانی last_login
            user = User.objects.get(id=serializer.validated_data['user_id'])
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return Response({
                "status": "success",
                "message": "ورود با موفقیت انجام شد",
                "data": serializer.validated_data
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": "کاربر یافت نشد"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطای سرور در ورود",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    """
    ویو برای خروج کاربر
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="خروج کاربر",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='توکن رفرش'
                )
            },
            required=['refresh']
        ),
        responses={
            200: 'خروج با موفقیت انجام شد',
            400: 'توکن نامعتبر یا وجود ندارد'
        }
    )
    def post(self, request):
        """
        خروج کاربر
        """
        try:
            refresh_token = request.data.get("refresh")
            
            if not refresh_token:
                return Response({
                    "status": "error",
                    "message": "توکن رفرش الزامی است"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                "status": "success",
                "message": "خروج با موفقیت انجام شد"
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response({
                "status": "error",
                "message": "توکن نامعتبر است"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در خروج",
                "errors": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    ویو برای مدیریت اطلاعات کاربر
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="دریافت اطلاعات کاربر",
        responses={
            200: UserDetailSerializer,
            500: 'خطای سرور'
        }
    )
    def get(self, request):
        """
        دریافت اطلاعات کاربر
        """
        try:
            serializer = UserDetailSerializer(request.user)
            
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در دریافت اطلاعات کاربر",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="بروزرسانی کامل اطلاعات کاربر",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('بروزرسانی موفق', UserProfileSerializer),
            400: 'اطلاعات نامعتبر'
        }
    )
    def put(self, request):
        """
        بروزرسانی کامل اطلاعات کاربر
        """
        return self._update_user(request, partial=False)

    @swagger_auto_schema(
        operation_description="بروزرسانی جزئی اطلاعات کاربر",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('بروزرسانی موفق', UserProfileSerializer),
            400: 'اطلاعات نامعتبر'
        }
    )
    def patch(self, request):
        """
        بروزرسانی جزئی اطلاعات کاربر
        """
        return self._update_user(request, partial=True)
    
    def _update_user(self, request, partial=False):
        """
        متد کمکی برای بروزرسانی کاربر
        """
        try:
            serializer = UserProfileSerializer(
                request.user, 
                data=request.data, 
                partial=partial
            )
            
            if not serializer.is_valid():
                return Response({
                    "status": "error",
                    "message": "اطلاعات وارد شده معتبر نیست",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            
            return Response({
                "status": "success",
                "message": "اطلاعات کاربر با موفقیت بروزرسانی شد",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در بروزرسانی اطلاعات کاربر",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordView(APIView):
    """
    ویو برای تغییر رمز عبور
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="تغییر رمز عبور کاربر",
        request_body=ChangePasswordSerializer,
        responses={
            200: 'رمز عبور با موفقیت تغییر یافت',
            400: 'خطا در اعتبارسنجی'
        }
    )
    def post(self, request):
        """
        تغییر رمز عبور
        """
        try:
            serializer = ChangePasswordSerializer(
                data=request.data, 
                context={'request': request}
            )
            
            if not serializer.is_valid():
                return Response({
                    "status": "error",
                    "message": "اطلاعات وارد شده معتبر نیست",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # تغییر رمز عبور
            serializer.save()
            
            return Response({
                "status": "success",
                "message": "رمز عبور با موفقیت تغییر یافت"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در تغییر رمز عبور",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomTokenRefreshView(TokenRefreshView):
    """
    ویو سفارشی برای رفرش توکن
    """

    @swagger_auto_schema(
        operation_description="رفرش توکن دسترسی",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['refresh']
        ),
        responses={
            200: 'توکن با موفقیت رفرش شد',
            400: 'توکن نامعتبر'
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                return Response({
                    "status": "success",
                    "message": "توکن با موفقیت رفرش شد",
                    "data": response.data
                })
            else:
                return Response({
                    "status": "error",
                    "message": "خطا در رفرش توکن",
                    "errors": response.data
                }, status=response.status_code)
                
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطای سرور در رفرش توکن",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserStatusView(APIView):
    """
    ویو برای بررسی وضعیت کاربر
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="بررسی وضعیت احراز هویت کاربر",
        responses={
            200: UserDetailSerializer,
            500: 'خطای سرور'
        }
    )
    def get(self, request):
        """
        بررسی وضعیت احراز هویت کاربر
        """
        try:
            serializer = UserProfileSerializer(request.user)
            
            return Response({
                "status": "success",
                "message": "کاربر لاگین است",
                "data": {
                    "user": serializer.data,
                    "is_authenticated": True,
                    "is_admin": request.user.is_admin
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در بررسی وضعیت کاربر",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Admin Views ---

class AdminUserManagementView(APIView):
    """
    ویو برای مدیریت کاربران توسط ادمین
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="دریافت لیست همه کاربران",
        responses={
            200: UserDetailSerializer(many=True),
            500: 'خطای سرور'
        }
    )
    def get(self, request):
        """
        دریافت لیست همه کاربران
        """
        try:
            users = User.objects.all().select_related('profile')
            serializer = UserDetailSerializer(users, many=True)
            
            return Response({
                "status": "success",
                "count": users.count(),
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در دریافت لیست کاربران",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="ایجاد کاربر جدید توسط ادمین",
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response('کاربر ایجاد شد', UserRegisterSerializer),
            400: 'اطلاعات نامعتبر'
        }
    )
    def post(self, request):
        """
        ایجاد کاربر جدید توسط ادمین
        """
        try:
            serializer = UserRegisterSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    "status": "error",
                    "message": "اطلاعات وارد شده معتبر نیست",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user_data = serializer.save()
            
            return Response({
                "status": "success",
                "message": "کاربر با موفقیت ایجاد شد",
                "data": user_data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در ایجاد کاربر",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminUserDetailView(APIView):
    """
    ویو برای مدیریت کاربر خاص توسط ادمین
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="دریافت اطلاعات کاربر خاص",
        responses={
            200: UserDetailSerializer,
            404: 'کاربر یافت نشد'
        }
    )
    def get(self, request, user_id):
        """
        دریافت اطلاعات کاربر خاص
        """
        try:
            user = get_object_or_404(User, id=user_id)
            serializer = UserDetailSerializer(user)
            
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": "کاربر یافت نشد"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در دریافت اطلاعات کاربر",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="بروزرسانی کاربر خاص",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('بروزرسانی موفق', UserProfileSerializer),
            400: 'اطلاعات نامعتبر'
        }
    )
    def patch(self, request, user_id):
        """
        بروزرسانی کاربر خاص
        """
        try:
            user = get_object_or_404(User, id=user_id)
            serializer = UserProfileSerializer(
                user, 
                data=request.data, 
                partial=True
            )
            
            if not serializer.is_valid():
                return Response({
                    "status": "error",
                    "message": "اطلاعات وارد شده معتبر نیست",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            
            return Response({
                "status": "success",
                "message": "کاربر با موفقیت بروزرسانی شد",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": "کاربر یافت نشد"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در بروزرسانی کاربر",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="حذف کاربر",
        responses={
            200: 'کاربر با موفقیت حذف شد',
            400: 'خطا در حذف کاربر'
        }
    )
    def delete(self, request, user_id):
        """
        حذف کاربر
        """
        try:
            user = get_object_or_404(User, id=user_id)
            
            # جلوگیری از حذف خود ادمین
            if user == request.user:
                return Response({
                    "status": "error",
                    "message": "نمی‌توانید حساب خودتان را حذف کنید"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user_email = user.email
            user.delete()
            
            return Response({
                "status": "success",
                "message": f"کاربر {user_email} با موفقیت حذف شد"
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": "کاربر یافت نشد"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در حذف کاربر",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserStatsView(APIView):
    """
    ویو برای آمار کاربران
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="دریافت آمار کاربران",
        responses={
            200: 'آمار کاربران',
            500: 'خطای سرور'
        }
    )
    def get(self, request):
        """
        دریافت آمار کاربران
        """
        try:
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            admin_users = User.objects.filter(is_admin=True).count()
            today_joined = User.objects.filter(
                date_joined__date=timezone.now().date()
            ).count()
            this_week_joined = User.objects.filter(
                date_joined__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
            
            stats = {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "admin_users": admin_users,
                "regular_users": total_users - admin_users,
                "today_joined": today_joined,
                "this_week_joined": this_week_joined,
                "active_percentage": round((active_users / total_users * 100), 2) if total_users > 0 else 0
            }
            
            return Response({
                "status": "success",
                "data": stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در دریافت آمار",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileViewSet(ModelViewSet):
    """
    ویوست کامل برای مدیریت پروفایل کاربر
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        """
        کاربر فقط می‌تواند پروفایل خودش را ببیند
        """
        if getattr(self, 'swagger_fake_view', False):
            return Profile.objects.none()
        
        return Profile.objects.filter(user=self.request.user)
    
    def get_object(self):
        """
        بازگرداندن پروفایل کاربر جاری
        """
        if getattr(self, 'swagger_fake_view', False):
            return Profile()
        
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def list(self, request, *args, **kwargs):
        """
        غیرفعال کردن لیست همه پروفایل‌ها
        """
        return Response({
            "status": "error",
            "message": "این عملیات مجاز نیست"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @swagger_auto_schema(
        operation_description="دریافت پروفایل کاربر جاری",
        responses={200: ProfileSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """
        دریافت پروفایل کاربر جاری
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'request': request})
            
            return Response({
                "status": "success",
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در دریافت پروفایل",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="بروزرسانی کامل پروفایل",
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer}
    )
    def update(self, request, *args, **kwargs):
        """
        بروزرسانی کامل پروفایل
        """
        return self._update_profile(request, partial=False)

    @swagger_auto_schema(
        operation_description="بروزرسانی جزئی پروفایل",
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        """
        بروزرسانی جزئی پروفایل
        """
        return self._update_profile(request, partial=True)
    
    def _update_profile(self, request, partial=False):
        """
        متد کمکی برای بروزرسانی پروفایل
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, 
                data=request.data, 
                partial=partial,
                context={'request': request}
            )
            
            if not serializer.is_valid():
                return Response({
                    "status": "error",
                    "message": "اطلاعات وارد شده معتبر نیست",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            
            return Response({
                "status": "success",
                "message": "پروفایل با موفقیت بروزرسانی شد",
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در بروزرسانی پروفایل",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="دریافت پروفایل کاربر جاری",
        responses={200: ProfileSerializer}
    )
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """
        دریافت پروفایل کاربر جاری
        """
        return self.retrieve(request)

    @swagger_auto_schema(
        operation_description="آپلود آواتار",
        manual_parameters=[
            openapi.Parameter(
                'avatar',
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='آواتار کاربر'
            )
        ],
        consumes=['multipart/form-data'],
        responses={200: ProfileSerializer}
    )
    @action(detail=False, methods=['post'])
    def upload_avatar(self, request):
        """
        آپلود آواتار
        """
        try:
            profile = self.get_object()
            
            if 'avatar' not in request.FILES:
                return Response({
                    "status": "error",
                    "message": "فایل آواتار الزامی است"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # حذف آواتار قبلی اگر وجود دارد
            if profile.avatar:
                profile.avatar.delete(save=False)
            
            profile.avatar = request.FILES['avatar']
            profile.save()
            
            serializer = self.get_serializer(profile, context={'request': request})
            
            return Response({
                "status": "success",
                "message": "آواتار با موفقیت آپلود شد",
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در آپلود آواتار",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="حذف آواتار",
        responses={
            200: 'آواتار با موفقیت حذف شد',
            400: 'آواتاری برای حذف وجود ندارد'
        }
    )
    @action(detail=False, methods=['delete'])
    def remove_avatar(self, request):
        """
        حذف آواتار
        """
        try:
            profile = self.get_object()
            
            if not profile.avatar:
                return Response({
                    "status": "error",
                    "message": "آواتاری برای حذف وجود ندارد"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            profile.avatar.delete(save=False)
            profile.avatar = None
            profile.save()
            
            serializer = self.get_serializer(profile, context={'request': request})
            
            return Response({
                "status": "success",
                "message": "آواتار با موفقیت حذف شد",
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در حذف آواتار",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="دریافت آمار پروفایل",
        responses={200: 'آمار پروفایل'}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        دریافت آمار پروفایل
        """
        try:
            profile = self.get_object()
            
            completion_data = self._calculate_profile_completion(profile)
            
            return Response({
                "status": "success",
                "data": completion_data
            })
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطا در دریافت آمار پروفایل",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_profile_completion(self, profile):
        """
        محاسبه درصد تکمیل پروفایل
        """
        fields = [
            ('bio', 'بیوگرافی', 15),
            ('avatar', 'آواتار', 20),
            ('phone_number', 'شماره تماس', 15),
            ('birth_date', 'تاریخ تولد', 15),
            ('gender', 'جنسیت', 10),
            ('website', 'وبسایت', 10),
            ('location', 'محل سکونت', 15)
        ]
        
        completed_score = 0
        total_score = sum(score for _, _, score in fields)
        completed_fields = []
        missing_fields = []
        
        for field_name, field_label, score in fields:
            field_value = getattr(profile, field_name)
            if field_value and str(field_value).strip():
                completed_score += score
                completed_fields.append(field_label)
            else:
                missing_fields.append(field_label)
        
        completion_percentage = round((completed_score / total_score) * 100, 1)
        
        return {
            "completion_percentage": completion_percentage,
            "completed_score": completed_score,
            "total_score": total_score,
            "completed_fields": completed_fields,
            "missing_fields": missing_fields,
            "level": self._get_profile_level(completion_percentage)
        }
    
    def _get_profile_level(self, percentage):
        """
        تعیین سطح پروفایل بر اساس درصد تکمیل
        """
        if percentage >= 90:
            return "طلایی"
        elif percentage >= 70:
            return "نقره‌ای"
        elif percentage >= 50:
            return "برنزی"
        else:
            return "ابتدایی"