"""
With these settings, tests run faster.
"""

from .base import *  # noqa pylint: disable=wildcard-import,unused-wildcard-import
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
# Admin site is only enabled during development
INSTALLED_APPS += ["django.contrib.admin"]  # noqa F405

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[-1]["OPTIONS"]["loaders"] = [  # type: ignore[index] # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Your stuff...
# ------------------------------------------------------------------------------
# Testing hooks requires a github token
WEBISCITE_GITHUB_TOKEN = "ABC123"
