"""This module handles the logic behind the constitution.

This contains methods to read the constitution as a dict, check which files in
a diff contain constitutional amendments, and automatically update the
constitution for changes which edit files included in the constitution without
resulting in constitutional amendments
"""

import json
from typing import TYPE_CHECKING
from typing import cast

from django.conf import settings
from unidiff import Hunk
from unidiff import PatchedFile
from unidiff import PatchSet

if TYPE_CHECKING:
    from pathlib import Path  # pragma: no cover

# Each filename corresponds to a list of pairs representing protected line
# ranges within that file, or None to protect the entire file


def _check_hunks(hunks: PatchedFile, locks: list[list[int]]) -> bool:
    """Check if any portions of an edit overlap with constitutional protections"""
    HUNK_MIN_LENGTH = 7  # noqa: N806
    for hunk in hunks:
        hunk = cast(Hunk, hunk)
        # diff shows 3 lines above and below for context
        # If the diff starts beyond line 1, remove the top 3 lines
        start = 1 if hunk.source_start == 1 else hunk.source_start + 3

        # Subtract 1 from start because it's not 0-indexed
        end = start + hunk.source_length - 1
        # The following statements removed context lines. They won't catch all of them
        # but are good enough

        # If start is not line 1, subtract 3 from source_length to ignore start context
        if start != 1:
            end -= 3

        # If diff is >= 7 lines, ignore end context (otherwise it reached EOF)
        if hunk.source_length >= HUNK_MIN_LENGTH:
            end -= 3

        for lock in locks:
            # If any of the diff is within or contains the protected range, return True
            start_prot = lock[0] <= start <= lock[1]
            end_prot = lock[0] <= end <= lock[1]
            full_prot = start <= lock[0] and lock[1] <= end
            if any((start_prot, end_prot, full_prot)):
                return True

    return False


def read_constitution() -> dict[str, list[list[int]] | None]:
    """Read the constitution and return it as a type-annotated dict"""
    path: Path = settings.BASE_DIR / "constitution.json"
    with path.open() as f:
        return json.load(f)


def is_constitutional(diff_str: str) -> list[str]:
    """Check which files include changes protected by the constitution

    Args:
        diff_str: A string containing the output of a git diff

    Returns:
        list[str]: A list containing the paths of files relative to the root of the
        repository which include consitutionally protected edits
    """
    constitution = read_constitution()
    patch = PatchSet(diff_str)
    matched_files: list[str] = []

    for file in patch:
        file = cast(PatchedFile, file)
        # Remove "a/" from start of source file path
        filepath = file.source_file[2:] if file.is_rename else file.path
        if filepath in constitution:
            locks = constitution[filepath]

            if (
                file.is_removed_file
                or file.is_rename
                or locks is None  # If the file is fully protected
                or _check_hunks(file, locks)  # If a protected hunk was edited
            ):
                matched_files.append(filepath)

    return matched_files


def update_constitution(diff_str: str) -> str:
    """Automatically update the constitution

    If a commit edits a file which has some portions protected by the constitution, but
    does not edit those portions, this method will update the constitution to ensure
    the same pieces of code remain covered.

    For example, say the constitution protects "foo.py" on lines 9 and 10, but a change
    is made where a line is added between lines 4 and 5. The change is not a
    constitutional amendment, so the constitution will be altered to protect lines 10
    and 11, ensuring the contents of the protected block remain consistent.

    Args:
        diff_str: A string containing the output of a git diff

    Returns:
        str: A JSON string containing the updated constitution, or an empty string if no
        updates are needed
    """
    constitution = read_constitution()
    patch = PatchSet(diff_str)
    update = False

    for file in patch:
        if file.path in constitution:
            locks = constitution[file.path]
            if locks is None:
                continue
            for hunk in file:
                for lock in locks:
                    if hunk.source_start < lock[0]:
                        update = True
                        delta = hunk.added - hunk.removed
                        lock[0] += delta
                        lock[1] += delta

    # If no changes were necessary, return empty string to prevent file update
    return json.dumps(constitution, sort_keys=True) if update else ""
