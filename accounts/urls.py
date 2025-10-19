from django.urls import path, include

urlpatterns = [
    path('', include('accounts.api.v1.urls')),
]