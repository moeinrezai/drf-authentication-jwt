from django.urls import path
from . import views

app_name = 'accounts_api_v1' 

urlpatterns = [
    path('', views.api_status, name='api-status'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/detail/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]