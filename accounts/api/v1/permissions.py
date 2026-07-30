from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    دسترسی فقط برای کاربران عضو گروه 'admin'
    """

    message = "فقط ادمین‌ها مجاز به این عملیات هستند."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="admin").exists()
        )


class IsSupportUser(permissions.BasePermission):
    """
    دسترسی فقط برای کاربران عضو گروه 'support'
    """

    message = "فقط تیم پشتیبانی مجاز به این عملیات هستند."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="support").exists()
        )


class IsSuperUser(permissions.BasePermission):
    """
    دسترسی فقط برای سوپریوزرها
    """

    message = "فقط سوپریوزرها مجاز به این عملیات هستند."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsCustomAdmin(permissions.BasePermission):
    """
    دسترسی برای کاربرانی که مجوز سفارشی 'can_manage_custom_admin' دارند
    """

    message = "شما مجوز دسترسی به این بخش را ندارید."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm(
            "accounts.can_manage_custom_admin"
        )


class IsOwner(permissions.BasePermission):
    """
    دسترسی فقط به منابع خود کاربر
    """

    message = "فقط صاحب این منبع مجاز به این عملیات است."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
