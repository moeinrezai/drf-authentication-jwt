from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile

@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = ('email', 'name', 'is_active', 'is_admin', 'last_login')
    list_filter = ('is_admin', 'is_active', 'remember_me')
    search_fields = ('email', 'name')
    ordering = ('email',)
    

    filter_horizontal = ()
    

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'remember_me')}),
        (_('Permissions'), {'fields': ('is_active', 'is_admin')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'remember_me'),
        }),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'gender', 'location', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('user__email', 'user__name', 'phone_number', 'location')
    raw_id_fields = ('user',)