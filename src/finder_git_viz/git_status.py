"""Git status detection via subprocess."""

import subprocess


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
