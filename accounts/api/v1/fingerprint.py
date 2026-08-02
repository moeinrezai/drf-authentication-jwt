import hashlib
from django.conf import settings

def generate_fingerprint(request):
    ua = request.META.get('HTTP_USER_AGENT', '')
    ip = request.META.get('REMOTE_ADDR', '')

    client_fp = request.headers.get('X-Device-Fingerprint', '')
    raw = f"{ua}|{ip}|{client_fp}"
    secret = getattr(settings, 'JWT_FINGERPRINT_SECRET', 'default-fp-secret')
    return hashlib.sha256(f"{raw}|{secret}".encode()).hexdigest()