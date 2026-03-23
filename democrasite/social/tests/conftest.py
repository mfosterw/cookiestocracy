import pytest

from democrasite.social.models import Note
from democrasite.social.models import Person

from .factories import NoteFactory
from .factories import PersonFactory


@pytest.fixture
def note() -> Note:
    """Create a Note instance."""
    return NoteFactory.create()


@pytest.fixture
def person() -> Person:
    """Create a Person instance."""
    return PersonFactory.create()
