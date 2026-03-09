"""Glob matching for config include patterns."""

import fnmatch
from pathlib import Path


def path_matches_globs(rel_path: str, globs: list[str]) -> bool:
    """Check if path (relative to repo root) matches any include glob.

    Uses fnmatch for simple patterns; Path.match for ** support.
    Empty globs -> True (refresh all).
    """
    if not globs:
        return True

    path_str = str(Path(rel_path)).replace("\\", "/")
    path_obj = Path(rel_path)

    for pattern in globs:
        if fnmatch.fnmatch(path_str, pattern):
            return True
        if path_obj.match(pattern):
            return True
    return False
