"""Global context processors for the democrasite app."""

from django.conf import settings


def settings_context(_request):
    """Settings available by default to the templates context."""
    # Note: we intentionally do NOT expose the entire settings
    # to prevent accidental leaking of sensitive information
    return {
        "DEBUG": settings.DEBUG,
        "github_repo": settings.WEBISCITE_REPO,
    }
