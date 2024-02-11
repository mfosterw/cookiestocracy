"""Context processors for the Webiscite app."""

from django.conf import settings


def settings_context(_request):
    """Expose webiscite settings to the templates context."""
    return {
        "github_repo": settings.WEBISCITE_REPO,
    }
