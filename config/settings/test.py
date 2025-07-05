"""
With these settings, tests run faster.
"""

from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import TEMPLATES
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="hUkWn3nrp3hAdKAM9U7U0WlfeEZQd8MH70bwytZ33QK0S98N90YLeJWKSyGeNv5Z",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"
# Admin site is not available in production, but should still be tested
INSTALLED_APPS += ["django.contrib.admin"]

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
# Required to have "debug=True" in tempalte context
INTERNAL_IPS = ["127.0.0.1"]
