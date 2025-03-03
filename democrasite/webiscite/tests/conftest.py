import pytest

from democrasite.webiscite.models import Bill

from .factories import BillFactory


@pytest.fixture
def bill() -> Bill:
    """Create a Bill instance with status 'open'"""
    return BillFactory.create()
