import pytest

from ..models import Bill
from .factories import BillFactory


@pytest.fixture
def bill() -> Bill:
    return BillFactory()
