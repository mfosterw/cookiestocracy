import pytest

from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):  # pylint: disable=unused-argument
    pass


@pytest.fixture
def user() -> User:
    return UserFactory()
