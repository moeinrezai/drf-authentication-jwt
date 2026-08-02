from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .fingerprint import generate_fingerprint
from django.utils.translation import gettext_lazy as _

class CookieOrHeaderJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = None
        if getattr(request, "device_type", None) == "web":
            raw_token = request.COOKIES.get("access_token")
        else:
            header = self.get_header(request)
            if header is not None:
                raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        token_fp = validated_token.get('fp')
        if token_fp:
            current_fp = generate_fingerprint(request)
            if current_fp != token_fp:
                raise AuthenticationFailed(_("نقص در اعتبار دستگاه. لطفاً دوباره وارد شوید."))

        return self.get_user(validated_token), validated_token