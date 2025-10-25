# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from .models import User, Profile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email',
        'name',
        'is_active',
        'is_admin',
        'last_login',
        'date_joined',
        'profile_link'
    )
    list_filter = (
        'is_admin',
        'is_active',
        'date_joined',
        'last_login'
    )
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    list_per_page = 25
    list_editable = ('is_active',)
    actions = ['activate_users', 'deactivate_users', 'make_admin', 'remove_admin']

    # حذف فیلدهای غیرضروری
    filter_horizontal = ()
    filter_vertical = ()

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('اطلاعات شخصی'), {
            'fields': ('name',)
        }),
        (_('دسترسی‌ها'), {
            'fields': ('is_active', 'is_admin', 'is_superuser')
        }),
        (_('تاریخ‌های مهم'), {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')

    def profile_link(self, obj):
        if hasattr(obj, 'profile'):
            url = reverse('admin:accounts_profile_change', args=[obj.profile.id])
            return format_html(
                '<a href="{}" style="background-color: #4CAF50; color: white; padding: 2px 6px; '
                'border-radius: 4px; text-decoration: none; font-size: 0.85em;">👤 پروفایل</a>',
                url
            )
        return "—"
    profile_link.short_description = _("پروفایل")

    # Actions
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _("%(count)d کاربر با موفقیت فعال شدند.") % {'count': updated},
            messages.SUCCESS
        )
    activate_users.short_description = _("فعال کردن کاربران انتخاب‌شده")

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _("%(count)d کاربر با موفقیت غیرفعال شدند.") % {'count': updated},
            messages.WARNING
        )
    deactivate_users.short_description = _("غیرفعال کردن کاربران انتخاب‌شده")

    def make_admin(self, request, queryset):
        updated = queryset.update(is_admin=True)
        self.message_user(
            request,
            _("دسترسی ادمین به %(count)d کاربر اعطا شد.") % {'count': updated},
            messages.SUCCESS
        )
    make_admin.short_description = _("اعطای دسترسی ادمین")

    def remove_admin(self, request, queryset):
        if request.user in queryset:
            self.message_user(
                request,
                _("نمی‌توانید دسترسی ادمین خودتان را حذف کنید."),
                messages.ERROR
            )
            queryset = queryset.exclude(id=request.user.id)
        updated = queryset.update(is_admin=False)
        if updated > 0:
            self.message_user(
                request,
                _("دسترسی ادمین از %(count)d کاربر حذف شد.") % {'count': updated},
                messages.WARNING
            )
    remove_admin.short_description = _("حذف دسترسی ادمین")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'user_name',
        'phone_number',
        'location',
        'created_at',
        'avatar_preview'
    )
    list_filter = (
        'created_at',
        'updated_at'
    )
    search_fields = (
        'user__email',
        'user__name',
        'phone_number',
        'location',
        'bio'
    )
    list_per_page = 20
    list_editable = ('phone_number', 'location')
    actions = ['clear_avatars', 'clear_bio']

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('اطلاعات تماس'), {
            'fields': ('phone_number', 'website', 'location')
        }),
        (_('اطلاعات شخصی'), {
            'fields': ('bio', 'birth_date')
        }),
        (_('مدیریت رسانه'), {
            'fields': ('avatar', 'avatar_preview')
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    readonly_fields = ('user_email', 'user_name', 'created_at', 'updated_at', 'avatar_preview')

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "—"
    avatar_preview.short_description = _("پیش‌نمایش آواتار")

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _("ایمیل کاربر")
    user_email.admin_order_field = 'user__email'

    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = _("نام کاربر")
    user_name.admin_order_field = 'user__name'

    def clear_avatars(self, request, queryset):
        count = 0
        for profile in queryset:
            if profile.avatar:
                profile.avatar.delete(save=False)
                profile.avatar = ''
                profile.save()
                count += 1
        self.message_user(
            request,
            _("آواتار %(count)d پروفایل با موفقیت حذف شد.") % {'count': count},
            messages.SUCCESS
        )
    clear_avatars.short_description = _("حذف آواتارهای انتخاب‌شده")

    def clear_bio(self, request, queryset):
        updated = queryset.update(bio='')
        self.message_user(
            request,
            _("بیوگرافی %(count)d پروفایل پاک شد.") % {'count': updated},
            messages.SUCCESS
        )
    clear_bio.short_description = _("پاک کردن بیوگرافی‌های انتخاب‌شده")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# سفارشی‌سازی عنوان‌های ادمین
admin.site.site_header = _("پنل مدیریت سیستم احراز هویت")
admin.site.site_title = _("سیستم احراز هویت")
admin.site.index_title = _("خوش آمدید به پنل مدیریت")