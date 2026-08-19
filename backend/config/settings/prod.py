from .base import *  # noqa: F401,F403

DEBUG = False

# nginx termina TLS y proxya a Django por HTTP en localhost; sin esto,
# SECURE_SSL_REDIRECT crea un loop de redirects (Django ve cada request como HTTP).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "https://tribuparidas.com,https://www.tribuparidas.com")  # noqa: F405
