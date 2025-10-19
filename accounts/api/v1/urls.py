from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .import views

router = DefaultRouter()
router.register(r'profiles', views.ProfileViewSet, basename='profile')

urlpatterns = [

    path('register', views.RegisterView.as_view(), name='register'),
    path('login', views.LoginView.as_view(), name='login'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('token/refresh', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('status', views.UserStatusView.as_view(), name='user_status'),

    path('profile', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/change-password', views.ChangePasswordView.as_view(), name='change_password'),

    path('admin/users', views.AdminUserManagementView.as_view(), name='admin_users'),
    path('admin/users/<int:user_id>', views.AdminUserManagementView.as_view(), name='admin_user_detail'),
    path('admin/stats', views.UserStatsView.as_view(), name='user_stats'),
    

    path('', include(router.urls)),
]