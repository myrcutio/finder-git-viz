"""Repo root discovery by matching path segments to remote.origin.url."""

import subprocess
from pathlib import Path


def find_repo_root(path: str) -> str | None:
    """Find the git repo root containing the given path.

    Walks path segments from the changed file upward. For each directory D
    with basename B: (1) D has .git, (2) B matches last segment of
    remote.origin.url (split by /, drop .git). Returns nearest match.

    Returns None if no repo found.
    """
    current = Path(path).resolve()
    if current.is_file():
        current = current.parent

    for parent in [current, *current.parents]:
        git_dir = parent / ".git"
        if not git_dir.exists():
            continue

        url_last = _get_remote_origin_last_segment(str(parent))
        if url_last is None or parent.name == url_last:
            return str(parent)

    return None


def _get_remote_origin_last_segment(repo_path: str) -> str | None:
    """Get last segment of remote.origin.url (e.g. 'repo-name' from '.../repo-name.git')."""
    result = subprocess.run(
        ["git", "config", "remote.origin.url"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None

    url = result.stdout.strip()
    # Handle git@host:org/repo.git or https://host/org/repo.git
    last = url.rstrip("/").split("/")[-1]
    return last.replace(".git", "") if last else None
