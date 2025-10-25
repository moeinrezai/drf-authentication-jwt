
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [

    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('me/', views.UserProfileView.as_view(), name='user-profile'),

    path('profile/', views.ProfileDetailView.as_view(), name='profile-detail'),


    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]