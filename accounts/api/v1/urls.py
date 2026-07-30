from django.urls import path
from . import views

app_name = "accounts_v1"

urlpatterns = [
    path("csrf/", views.CsrfTokenView.as_view(), name="csrf"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("refresh/", views.RefreshView.as_view(), name="refresh"),
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change_password"
    ),
    path(
        "forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"
    ),
    path(
        "reset-password/",
        views.ResetPasswordConfirmView.as_view(),
        name="reset_password",
    ),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
