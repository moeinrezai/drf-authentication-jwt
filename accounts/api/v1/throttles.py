from rest_framework.throttling import ScopedRateThrottle


class LoginRateThrottle(ScopedRateThrottle):
    scope = "login"


class RefreshRateThrottle(ScopedRateThrottle):
    scope = "refresh"


class LogoutRateThrottle(ScopedRateThrottle):
    scope = "logout"
