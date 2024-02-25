import pytest

from democrasite.webiscite.models import Bill

from .factories import BillFactory


@pytest.fixture()
def bill() -> Bill:
    return BillFactory()
