"""Event handler: on FSEvent, resolve config, match globs, debounce, refresh tag."""

import threading
from pathlib import Path

from .config import resolve_config
from .git_status import get_git_status
from .globs import path_matches_globs
from .repo_root import find_repo_root
from .status_mapping import git_status_to_tag
from .tags import set_finder_tag

DEBOUNCE_SECONDS = 3.0
_pending: dict[str, threading.Timer] = {}
_lock = threading.Lock()


def _refresh_tag(repo_path: str) -> None:
    """Get git status, map to color and tag name, set Finder tag."""
    try:
        status = get_git_status(repo_path)
        color, tag_name = git_status_to_tag(status, repo_path)
        set_finder_tag(repo_path, tag_name, color)
    except Exception:
        pass  # Log or ignore


def _schedule_refresh(repo_path: str) -> None:
    """Schedule a refresh in DEBOUNCE_SECONDS. Cancel previous if any."""
    with _lock:
        if repo_path in _pending:
            _pending[repo_path].cancel()

        def run():
            with _lock:
                if repo_path in _pending:
                    del _pending[repo_path]
            _refresh_tag(repo_path)

        t = threading.Timer(DEBOUNCE_SECONDS, run)
        _pending[repo_path] = t
        t.start()


def on_path_event(event_path: str) -> None:
    """Handle a file system event at the given path.

    1. Find repo root
    2. Resolve config, check globs
    3. If match: debounce and refresh tag
    """
    repo_root = find_repo_root(event_path)
    if not repo_root:
        return

    config = resolve_config(repo_root)
    globs = config.get("include", {}).get("globs", ["**"])

    try:
        rel_path = str(Path(event_path).relative_to(repo_root))
    except ValueError:
        return  # event_path not under repo_root

    if not path_matches_globs(rel_path, globs):
        return

    _schedule_refresh(repo_root)


def refresh_repo(repo_path: str) -> None:
    """Refresh tag for a repo immediately (one-shot, no debounce)."""
    _refresh_tag(repo_path)
