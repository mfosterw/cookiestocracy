# pylint: disable=too-few-public-methods,no-self-use
from os.path import isfile
from unittest.mock import patch

from django.conf import settings
from unidiff import PatchSet

from .. import constitution
from ..constitution import (
    _check_hunks,
    is_constitutional,
    read_constitution,
    update_constitution,
)


class TestCheckHunks:
    def test_short_file_start(self):
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -1,5 +1,4 @@
 This is the original content.

-This should be updated.

 This will stay."""
        file = PatchSet(diff)[0]
        start_lock = [[1, 1]]

        assert _check_hunks(file, start_lock)

        end_lock = [[5, 5]]

        assert _check_hunks(file, end_lock)

        bad_lock = [[6, 6]]

        assert not _check_hunks(file, bad_lock)

    def test_long_file_start(self):
        # Long refers to being long enough to include the full 6 lines of context
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -1,7 +1,6 @@
 This is the original content.
 This is more content.

-This should be updated.

 This will stay.
 This will also stay."""
        file = PatchSet(diff)[0]
        start_lock = [[1, 1]]

        assert _check_hunks(file, start_lock)

        edit_lock = [[4, 4]]  # The actual altered line

        assert _check_hunks(file, edit_lock)

        end_lock = [[5, 5]]

        # Since the diff is >=7 lines, the ending context should be ignored
        assert not _check_hunks(file, end_lock)

    def test_short_file(self):
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -3,6 +3,5 @@
 This is the original content.
 This is more content.

-This should be updated.

 This will stay."""
        file = PatchSet(diff)[0]
        start_lock = [[5, 5]]

        # Since the diff start != 1, the beginning context should be ignored
        assert not _check_hunks(file, start_lock)

        edit_lock = [[6, 6]]

        assert _check_hunks(file, edit_lock)

        end_lock = [[8, 8]]

        assert _check_hunks(file, end_lock)

    def test_long_file(self):
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -3,7 +3,6 @@
 This is the original content.
 This is more content.

-This should be updated.

 This will stay.
 This will also stay."""
        file = PatchSet(diff)[0]
        start_lock = [[5, 5]]
        # All context should be ignored in this diff

        assert not _check_hunks(file, start_lock)

        edit_lock = [[6, 6]]

        assert _check_hunks(file, edit_lock)

        end_lock = [[7, 7]]

        assert not _check_hunks(file, end_lock)

    def test_long_diff(self):
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -3,9 +3,6 @@
 This is the original content.
 This is more content.

-This should be updated.
-This is getting removed.
-This is going bye-bye

 This will stay.
 This will also stay."""
        file = PatchSet(diff)[0]
        start_lock = [[5, 5]]
        # All context should be ignored in this diff

        assert not _check_hunks(file, start_lock)

        within_edit_lock = [[7, 7]]

        assert _check_hunks(file, within_edit_lock)

        around_edit_lock = [[5, 9]]

        assert _check_hunks(file, around_edit_lock)

        end_lock = [[9, 9]]

        assert not _check_hunks(file, end_lock)


class TestIsConstitutional:
    @patch.object(constitution, "read_constitution")
    def test_file_lock_removed(self, mock_constitution):
        diff = """diff --git a/removed_file b/removed_file
deleted file mode 100644
index 1f38447..0000000
--- a/removed_file
+++ /dev/null
@@ -1,3 +0,0 @@
-This content shouldn't be here.
-
-This file will be removed."""
        mock_constitution.return_value = {"removed_file": [[15, 15]]}

        assert is_constitutional(diff) == ["removed_file"]

    @patch.object(constitution, "read_constitution")
    def test_file_lock_renamed(self, mock_constitution):
        diff = """diff --git a/added_file b/moved_file
similarity index 85%
rename from added_file
rename to moved_file
index a071991..4dbab21 100644
--- a/added_file
+++ b/moved_file
@@ -9,4 +9,4 @@ Some content
 Some content
 Some content
 Some content
-Some content
+Some modified content"""
        mock_constitution.return_value = {"added_file": [[15, 15]]}

        assert is_constitutional(diff) == ["added_file"]

    @patch.object(constitution, "read_constitution")
    def test_whole_file_locked(self, mock_constitution):
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -1,5 +1,4 @@
 This is the original content.

-This should be updated.

 This will stay."""
        mock_constitution.return_value = {"modified_file": None}

        assert is_constitutional(diff) == ["modified_file"]

    @patch.object(constitution, "read_constitution")
    def test_hunk_locked(self, mock_constitution):
        # This is basically an integration test, mainly for 100% coverage
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -1,5 +1,4 @@
 This is the original content.

-This should be updated.

 This will stay."""
        mock_constitution.return_value = {"modified_file": [[3, 3]]}

        assert is_constitutional(diff) == ["modified_file"]

    @patch.object(constitution, "read_constitution")
    def test_file_not_locked(self, mock_constitution):
        diff = """diff --git a/removed_file b/removed_file
deleted file mode 100644
index 1f38447..0000000
--- a/removed_file
+++ /dev/null
@@ -1,3 +0,0 @@
-This content shouldn't be here.
-
-This file will be removed."""
        mock_constitution.return_value = {}

        assert is_constitutional(diff) == []


class TestUpdateConstitution:
    @patch.object(constitution, "read_constitution")
    def test_whole_file_locked(self, mock_constitution):
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -1,5 +1,4 @@
 This is the original content.

-This should be updated.

 This will stay."""
        mock_constitution.return_value = {"modified_file": None}

        assert update_constitution(diff) == ""

    @patch.object(constitution, "read_constitution")
    def test_file_updated(self, mock_constitution):
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -1,5 +1,4 @@
 This is the original content.

-This should be updated.

 This will stay."""
        mock_constitution.return_value = {"modified_file": [[15, 15]]}

        assert update_constitution(diff) == '{"modified_file": [[14, 14]]}'

    @patch.object(constitution, "read_constitution")
    def test_file_not_locked(self, mock_constitution):
        diff = """diff --git a/modified_file b/modified_file
index c7921f5..8946660 100644
--- a/modified_file
+++ b/modified_file
@@ -1,5 +1,4 @@
 This is the original content.

-This should be updated.

 This will stay."""
        mock_constitution.return_value = {}

        assert update_constitution(diff) == ""


class TestConstitutionFiles:
    def test_constitution_files(self):
        """Ensure the files in constitution.json exist (does not check line numbers)"""
        for file in read_constitution():
            assert isfile(
                settings.ROOT_DIR / file
            ), f"{file} from constitution.json not found"
