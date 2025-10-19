from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html
from .models import User, Profile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # نمایش در لیست
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
        'remember_me',
        'date_joined',
        'last_login'
    )
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    list_per_page = 25
    
    # 🔥 اصلاح: حذف filter_horizontal یا تعریف خالی
    filter_horizontal = ()
    
    # فیلدهای قابل ویرایش در لیست
    list_editable = ('is_active',)
    
    # actions سفارشی
    actions = ['activate_users', 'deactivate_users', 'make_admin', 'remove_admin']

    # fieldsets برای صفحه ویرایش
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('اطلاعات شخصی'), {
            'fields': ('name', 'remember_me')
        }),
        (_('دسترسی‌ها'), {
            'fields': ('is_active', 'is_admin')
        }),
        (_('تاریخ‌های مهم'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # fieldsets برای صفحه ایجاد کاربر
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'remember_me'),
        }),
    )
    
    # فیلدهای فقط خواندنی
    readonly_fields = ('last_login', 'date_joined')
    
    def profile_link(self, obj):
        """لینک به پروفایل کاربر"""
        if hasattr(obj, 'profile'):
            url = f"/admin/accounts/profile/{obj.profile.id}/change/"
            return format_html(
                '<a href="{}" style="background-color: #4CAF50; color: white; padding: 2px 6px; border-radius: 4px; text-decoration: none;">👤 پروفایل</a>',
                url
            )
        return "—"
    profile_link.short_description = "پروفایل"
    profile_link.allow_tags = True

    def activate_users(self, request, queryset):
        """فعال کردن کاربران انتخاب شده"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} کاربر با موفقیت فعال شدند', 
            messages.SUCCESS
        )
    activate_users.short_description = "فعال کردن کاربران انتخاب شده"

    def deactivate_users(self, request, queryset):
        """غیرفعال کردن کاربران انتخاب شده"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} کاربر با موفقیت غیرفعال شدند', 
            messages.WARNING
        )
    deactivate_users.short_description = "غیرفعال کردن کاربران انتخاب شده"

    def make_admin(self, request, queryset):
        """اعطای دسترسی ادمین به کاربران انتخاب شده"""
        updated = queryset.update(is_admin=True)
        self.message_user(
            request, 
            f'دسترسی ادمین به {updated} کاربر اعطا شد', 
            messages.SUCCESS
        )
    make_admin.short_description = "اعطای دسترسی ادمین"

    def remove_admin(self, request, queryset):
        """حذف دسترسی ادمین از کاربران انتخاب شده"""
        # جلوگیری از حذف دسترسی ادمین از خود کاربر
        if request.user in queryset:
            self.message_user(
                request, 
                'نمی‌توانید دسترسی ادمین خودتان را حذف کنید', 
                messages.ERROR
            )
            queryset = queryset.exclude(id=request.user.id)
        
        updated = queryset.update(is_admin=False)
        if updated > 0:
            self.message_user(
                request, 
                f'دسترسی ادمین از {updated} کاربر حذف شد', 
                messages.WARNING
            )
    remove_admin.short_description = "حذف دسترسی ادمین"

    def get_queryset(self, request):
        """بهینه‌سازی کوئری‌ست"""
        return super().get_queryset(request).select_related('profile')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # نمایش در لیست
    list_display = (
        'user_email',
        'user_name',
        'phone_number',
        'gender_display',
        'location',
        'created_at',
        'avatar_preview'
    )
    list_filter = (
        'gender',
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
    
    # فیلدهای قابل ویرایش در لیست
    list_editable = ('phone_number', 'location')
    
    # fieldsets برای صفحه ویرایش
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('اطلاعات تماس'), {
            'fields': ('phone_number', 'website', 'location')
        }),
        (_('اطلاعات شخصی'), {
            'fields': ('bio', 'birth_date', 'gender')
        }),
        (_('مدیریت رسانه'), {
            'fields': ('avatar', 'avatar_preview')
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    # فیلدهای فقط خواندنی
    readonly_fields = ('user_email', 'user_name', 'created_at', 'updated_at', 'avatar_preview')
    
    # پیش‌نمایش آواتار
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "—"
    avatar_preview.short_description = "پیش‌نمایش آواتار"
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "ایمیل کاربر"
    user_email.admin_order_field = 'user__email'
    
    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = "نام کاربر"
    user_name.admin_order_field = 'user__name'
    
    def gender_display(self, obj):
        return obj.get_gender_display()
    gender_display.short_description = "جنسیت"
    gender_display.admin_order_field = 'gender'
    
    # actions سفارشی
    actions = ['clear_avatars', 'clear_bio']
    
    def clear_avatars(self, request, queryset):
        """حذف آواتارهای انتخاب شده"""
        updated = queryset.update(avatar='')
        self.message_user(
            request, 
            f'آواتار {updated} پروفایل حذف شد', 
            messages.SUCCESS
        )
    clear_avatars.short_description = "حذف آواتارهای انتخاب شده"
    
    def clear_bio(self, request, queryset):
        """حذف بیوگرافی‌های انتخاب شده"""
        updated = queryset.update(bio='')
        self.message_user(
            request, 
            f'بیوگرافی {updated} پروفایل حذف شد', 
            messages.SUCCESS
        )
    clear_bio.short_description = "حذف بیوگرافی‌های انتخاب شده"
    
    def get_queryset(self, request):
        """بهینه‌سازی کوئری‌ست"""
        return super().get_queryset(request).select_related('user')


# سفارشی‌سازی هدر ادمین
admin.site.site_header = "پنل مدیریت سیستم احراز هویت"
admin.site.site_title = "سیستم احراز هویت"
admin.site.index_title = "خوش آمدید به پنل مدیریت"