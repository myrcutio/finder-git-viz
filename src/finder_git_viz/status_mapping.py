"""Map git status porcelain output to Finder tag colors (0-7) and labels."""

from . import git_status

# Color codes: 0=none, 1=grey, 2=green, 3=purple, 4=blue, 5=yellow, 6=red, 7=orange
COLOR_NONE = 0
COLOR_GREY = 1
COLOR_GREEN = 2
COLOR_PURPLE = 3
COLOR_BLUE = 4
COLOR_YELLOW = 5
COLOR_RED = 6
COLOR_ORANGE = 7

# (color, tag_name) for each status — single source of truth
# Grey (not a repo) omitted — we only tag actual repos
STATUS_MAP = {
    "conflict": (COLOR_PURPLE, "git: conflicts / detached"),
    "staged_unstaged": (COLOR_RED, "git: unstaged changes"),
    "staged_only": (COLOR_ORANGE, "git: staged only"),
    "unstaged_only": (COLOR_RED, "git: unstaged changes"),
    "untracked_only": (COLOR_YELLOW, "git: untracked only"),
    "behind_main": (COLOR_BLUE, "git: behind main"),
    "up_to_date": (COLOR_GREEN, "git: up to date"),
}

# Priority order for resolving status (first match wins)
STATUS_PRIORITY = ["conflict", "staged_unstaged", "staged_only", "unstaged_only", "untracked_only"]


def _xy_to_status(xy: str) -> str | None:
    """Map git porcelain XY pair to status key, or None if clean."""
    if len(xy) < 2:
        return None
    x, y = xy[0], xy[1]
    match xy:
        case "UU" | "AA" | "DD" | "AU" | "UA" | "DU" | "UD":
            return "conflict"
        case "??":
            return "untracked_only"
        case _ if x not in " ?" and y not in " ?":
            return "staged_unstaged"
        case _ if x not in " ?":
            return "staged_only"
        case _ if y not in " ?":
            return "unstaged_only"
        case _:
            return None


def git_status_to_tag(status: str, repo_path: str | None = None) -> tuple[int, str]:
    """Map porcelain output to (color, tag_name).

    Priority (first match wins):
    - Conflict / detached / rebase -> Purple
    - Uncommitted (staged, unstaged) -> Red
    - Staged, not committed -> Orange
    - Untracked only -> Yellow
    - Behind origin/main -> Blue (needs pull)
    - Clean and up to date with main -> Green
    """
    lines = [ln.strip() for ln in status.strip().splitlines() if ln.strip()]

    if not lines:
        if repo_path and git_status.is_behind_origin_main(repo_path):
            return STATUS_MAP["behind_main"]
        return STATUS_MAP["up_to_date"]

    statuses = {_xy_to_status(line[:2]) for line in lines if len(line) >= 2}
    statuses.discard(None)
    resolved = next((s for s in STATUS_PRIORITY if s in statuses), None)

    if resolved is not None:
        return STATUS_MAP[resolved]
    if repo_path and git_status.is_behind_origin_main(repo_path):
        return STATUS_MAP["behind_main"]
    return STATUS_MAP["up_to_date"]
