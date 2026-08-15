from .base import *  # noqa: F401,F403

DEBUG = True

# En desarrollo es habitual entrar desde distintos hosts (docker, localhost, LAN).
if "*" not in ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ALLOWED_HOSTS + ["backend"]  # noqa: F405
