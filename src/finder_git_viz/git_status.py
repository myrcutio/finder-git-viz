"""Git status detection via subprocess."""

import subprocess
from pathlib import Path

_DEFAULT_BRANCH_NAMES = (
    "main",
    "trunk",
    "mainline",
    "default",
    "stable",
    "master",
)
_REF_PREFIXES = (
    "refs/heads/",
    "refs/remotes/origin/",
    "refs/remotes/upstream/",
)


def _git_show_ref_exists(repo_path: str, ref: str) -> bool:
    result = subprocess.run(
        ["git", "show-ref", "-q", "--verify", ref],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def resolve_default_branch_name(repo_path: str) -> str:
    """Best-effort default branch short name (matches common shell helper order).

    Tries local and remote tracking refs for known names, then origin/HEAD and
    upstream/HEAD, then falls back to 'master'.
    """
    for prefix in _REF_PREFIXES:
        for name in _DEFAULT_BRANCH_NAMES:
            if _git_show_ref_exists(repo_path, f"{prefix}{name}"):
                return name
    for remote in ("origin", "upstream"):
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", f"{remote}/HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            continue
        ref = result.stdout.strip()
        prefix = f"{remote}/"
        if ref.startswith(prefix):
            return ref.removeprefix(prefix)
    return "master"


def get_current_branch_or_none(repo_path: str) -> str | None:
    """Symbolic branch short name, or None if detached or error."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    name = result.stdout.strip()
    if not name or name == "HEAD":
        return None
    return name


def is_on_fixed_branch_not_default(repo_path: str) -> bool:
    """True if HEAD is a named branch and its name differs from the resolved default."""
    current = get_current_branch_or_none(repo_path)
    if current is None:
        return False
    return current != resolve_default_branch_name(repo_path)


def is_on_default_branch(repo_path: str) -> bool:
    """True if HEAD is a named branch matching the resolved default branch name."""
    current = get_current_branch_or_none(repo_path)
    if current is None:
        return False
    return current == resolve_default_branch_name(repo_path)


def _git_verify_ref(repo_path: str, ref: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", ref],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def repo_in_merge(repo_path: str) -> bool:
    """True if a merge is in progress (MERGE_HEAD)."""
    return _git_verify_ref(repo_path, "MERGE_HEAD")


def repo_in_rebase(repo_path: str) -> bool:
    """True if a rebase is in progress."""
    r = subprocess.run(
        ["git", "rev-parse", "--git-path", "rebase-merge"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return False
    p = Path(r.stdout.strip())
    if not p.is_absolute():
        p = Path(repo_path) / p
    if p.is_dir():
        return True
    r2 = subprocess.run(
        ["git", "rev-parse", "--git-path", "rebase-apply"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if r2.returncode != 0:
        return False
    p2 = Path(r2.stdout.strip())
    if not p2.is_absolute():
        p2 = Path(repo_path) / p2
    return p2.is_dir()


def repo_in_cherry_pick(repo_path: str) -> bool:
    return _git_verify_ref(repo_path, "CHERRY_PICK_HEAD")


def repo_in_revert(repo_path: str) -> bool:
    return _git_verify_ref(repo_path, "REVERT_HEAD")


def is_diverged_from_origin_default(repo_path: str) -> bool:
    """True if HEAD and origin/HEAD each have commits the other lacks."""
    result = subprocess.run(
        ["git", "rev-list", "--left-right", "--count", "HEAD...origin/HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return False
    try:
        ahead, behind = int(parts[0]), int(parts[1])
    except ValueError:
        return False
    return ahead > 0 and behind > 0


def is_behind_origin_main(repo_path: str) -> bool:
    """True if local branch is behind the default branch on origin.

    Uses origin/HEAD (the symbolic ref for the remote's default branch).
    If origin/HEAD doesn't exist (e.g. local-only repo), returns False.
    """
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD..origin/HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip().isdigit():
        return int(result.stdout.strip()) > 0
    return False


def get_git_status(repo_path: str) -> str:
    """Run git status --porcelain and return stdout.

    Returns empty string for clean repo.
    - ?? = untracked
    - First char M/A/D/R/C = staged changes
    - Second char = unstaged changes
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else ""
