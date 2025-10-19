from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.decorators import action

from ...models import User, Profile
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
    UserDetailSerializer
)


@extend_schema(
    request=UserRegisterSerializer,
    responses={201: UserRegisterSerializer, 400: dict}
)
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "اطلاعات وارد شده معتبر نیست",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        return Response({
            "status": "success",
            "message": "ثبت‌نام با موفقیت انجام شد",
            "data": serializer.data  # ✅ serializer.data, not user object
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    request=UserLoginSerializer,
    responses={200: dict, 400: dict, 404: dict}
)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "اطلاعات وارد شده معتبر نیست",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=serializer.validated_data['user_id'])
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            "status": "success",
            "message": "ورود با موفقیت انجام شد",
            "data": serializer.validated_data
        }, status=status.HTTP_200_OK)


@extend_schema(
    request={"refresh": "string"},
    responses={200: dict, 400: dict}
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({
                "status": "error",
                "message": "توکن رفرش الزامی است"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
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
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "status": "success",
            "message": "خروج با موفقیت انجام شد"
        }, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(request=UserProfileSerializer, responses={200: UserProfileSerializer, 400: dict})
    def put(self, request):
        return self._update_user(request, partial=False)

    @extend_schema(request=UserProfileSerializer, responses={200: UserProfileSerializer, 400: dict})
    def patch(self, request):
        return self._update_user(request, partial=True)

    def _update_user(self, request, partial=False):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=partial)
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


@extend_schema(
    request=ChangePasswordSerializer,
    responses={200: dict, 400: dict}
)
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "اطلاعات وارد شده معتبر نیست",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({
            "status": "success",
            "message": "رمز عبور با موفقیت تغییر یافت"
        }, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    @extend_schema(
        request={"refresh": "string"},
        responses={200: dict, 400: dict}
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return Response({
                "status": "success",
                "message": "توکن با موفقیت رفرش شد",
                "data": response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": "error",
                "message": "خطای سرور در رفرش توکن",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response({
            "status": "success",
            "message": "کاربر لاگین است",
            "data": {
                "user": serializer.data,
                "is_authenticated": True,
                "is_admin": request.user.is_admin
            }
        }, status=status.HTTP_200_OK)


# --- Admin Views ---

@extend_schema(responses={200: UserDetailSerializer(many=True)})
class AdminUserManagementView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.all().select_related('profile')
        serializer = UserDetailSerializer(users, many=True)
        return Response({
            "status": "success",
            "count": users.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(request=UserRegisterSerializer, responses={201: UserRegisterSerializer, 400: dict})
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "اطلاعات وارد شده معتبر نیست",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        return Response({
            "status": "success",
            "message": "کاربر با موفقیت ایجاد شد",
            "data": serializer.data  # ✅ serializer.data
        }, status=status.HTTP_201_CREATED)


@extend_schema(responses={200: UserDetailSerializer})
class AdminUserDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserDetailSerializer(user)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(request=UserProfileSerializer, responses={200: UserProfileSerializer, 400: dict})
    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
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

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
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


class UserStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        admin_users = User.objects.filter(is_admin=True).count()
        today_joined = User.objects.filter(date_joined__date=timezone.now().date()).count()
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


class ProfileViewSet(ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Profile.objects.none()
        return Profile.objects.filter(user=self.request.user)

    def get_object(self):
        if getattr(self, 'swagger_fake_view', False):
            return Profile()
        return get_object_or_404(Profile, user=self.request.user)

    def list(self, request, *args, **kwargs):
        return Response({
            "status": "error",
            "message": "این عملیات مجاز نیست"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        return self._update_profile(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        return self._update_profile(request, partial=True)

    def _update_profile(self, request, partial=False):
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

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        return self.retrieve(request)

    @action(detail=False, methods=['post'])
    def upload_avatar(self, request):
        if getattr(self, 'swagger_fake_view', False):
            return Response()
        profile = self.get_object()
        if 'avatar' not in request.FILES:
            return Response({
                "status": "error",
                "message": "فایل آواتار الزامی است"
            }, status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=False, methods=['delete'])
    def remove_avatar(self, request):
        if getattr(self, 'swagger_fake_view', False):
            return Response()
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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        if getattr(self, 'swagger_fake_view', False):
            return Response()
        profile = self.get_object()
        completion_data = self._calculate_profile_completion(profile)
        return Response({
            "status": "success",
            "data": completion_data
        })

    def _calculate_profile_completion(self, profile):
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
        if percentage >= 90:
            return "طلایی"
        elif percentage >= 70:
            return "نقره‌ای"
        elif percentage >= 50:
            return "برنزی"
        else:
            return "ابتدایی"


    from rest_framework.decorators import action
    my_profile = action(detail=False, methods=['get'])(my_profile)
    upload_avatar = action(detail=False, methods=['post'])(upload_avatar)
    remove_avatar = action(detail=False, methods=['delete'])(remove_avatar)
    stats = action(detail=False, methods=['get'])(stats)