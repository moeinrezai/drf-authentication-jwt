from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieOrHeaderJWTAuthentication(JWTAuthentication):
    """
    احراز هویت سفارشی JWT با پشتیبانی از هر دو حالت کوکی و هدر

    - وب (دسکتاپ): توکن access از کوکی access_token خوانده می‌شود
    - موبایل/تبلت: توکن access از هدر Authorization: Bearer <token> خوانده می‌شود
    """

    def authenticate(self, request):
        raw_token = None

        if getattr(request, 'device_type', None) == 'web':
         
            raw_token = request.COOKIES.get('access_token')
        else:
            
            header = self.get_header(request)
            if header is not None:
                raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None  

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token