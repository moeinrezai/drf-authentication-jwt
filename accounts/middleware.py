import re


class DeviceDetectionMiddleware:
    """
    میدلور تشخیص نوع دستگاه کاربر بر اساس User-Agent

    وظایف:
    1. تشخیص دستگاه موبایل/تبلت یا کامپیوتر
    2. تنظیم request.device_type به 'mobile' یا 'web'
    3. غیرفعال کردن بررسی CSRF برای دستگاه‌های موبایل
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        mobile_pattern = (
            r"Mobile|Android|iPhone|iPad|iPod|"
            r"webOS|BlackBerry|IEMobile|Opera Mini|"
            r"Windows Phone|Kindle|Silk"
        )

        if re.search(mobile_pattern, user_agent, re.IGNORECASE):
            request.device_type = "mobile"

            request._dont_enforce_csrf_checks = True
        else:
            request.device_type = "web"

        response = self.get_response(request)
        return response
