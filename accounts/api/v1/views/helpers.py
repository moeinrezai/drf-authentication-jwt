from django.conf import settings
jwt_settings = getattr(settings, "SIMPLE_JWT", {})
ACCESS_COOKIE = jwt_settings.get("AUTH_COOKIE", "access_token")
REFRESH_COOKIE = jwt_settings.get("AUTH_COOKIE_REFRESH", "refresh_token")
COOKIE_SAMESITE = jwt_settings.get("AUTH_COOKIE_SAMESITE", "Lax")
COOKIE_HTTPONLY = jwt_settings.get("AUTH_COOKIE_HTTP_ONLY", True)
COOKIE_SECURE = jwt_settings.get("AUTH_COOKIE_SECURE", not settings.DEBUG)
COOKIE_PATH = jwt_settings.get("AUTH_COOKIE_PATH", "/")


def set_auth_cookies(response, access_token, refresh_token):
    response.set_cookie(
        key=ACCESS_COOKIE, value=access_token,
        httponly=COOKIE_HTTPONLY, secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE, path=COOKIE_PATH,
    )
    response.set_cookie(
        key=REFRESH_COOKIE, value=refresh_token,
        httponly=COOKIE_HTTPONLY, secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE, path=COOKIE_PATH,
    )
    return response


def delete_auth_cookies(response):
    response.delete_cookie(ACCESS_COOKIE, path=COOKIE_PATH)
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
    return response
