"""Global test fixtures for the project."""

import pytest

from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    """Change the media root to a temporary directory."""
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):  # pylint: disable=unused-argument
    """Give all tests access to the database."""


@pytest.fixture
def user() -> User:
    """Return a User instance."""
    return UserFactory()
