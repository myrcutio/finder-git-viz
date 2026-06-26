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
STATUS_MAP = {
    "merge_conflict": (COLOR_RED, "git: merge conflict"),
    "merge_in_progress": (COLOR_RED, "git: merge in progress"),
    "rebase_in_progress": (COLOR_RED, "git: rebase in progress"),
    "cherry_pick": (COLOR_RED, "git: cherry-pick in progress"),
    "revert_in_progress": (COLOR_RED, "git: revert in progress"),
    "diverged": (COLOR_RED, "git: diverged from default"),
    "detached": (COLOR_RED, "git: detached HEAD"),
    "mixed_staged_unstaged": (COLOR_RED, "git: staged and unstaged changes"),
    "default_dirty": (COLOR_RED, "git: uncommitted on default branch"),
    "nondefault_dirty_behind": (COLOR_RED, "git: changes while behind default"),
    "behind_default": (COLOR_GREY, "git: behind default branch"),
    "up_to_date_default": (COLOR_GREEN, "git: clean on default branch"),
    "nondefault_clean_ahead": (COLOR_BLUE, "git: clean feature branch"),
    "nondefault_behind": (COLOR_ORANGE, "git: feature branch behind default"),
    "nondefault_staged": (COLOR_PURPLE, "git: staged on feature branch"),
    "nondefault_unstaged": (COLOR_YELLOW, "git: unstaged on feature branch"),
}


def _aggregate_porcelain(lines: list[str]) -> tuple[bool, bool, bool, bool]:
    """Return (has_conflict, has_staged, has_unstaged, has_untracked)."""
    has_conflict = False
    has_staged = False
    has_unstaged = False
    has_untracked = False
    for line in lines:
        if len(line) < 2:
            continue
        xy = line[:2]
        match xy:
            case "UU" | "AA" | "DD" | "AU" | "UA" | "DU" | "UD":
                has_conflict = True
            case "??":
                has_untracked = True
            case _:
                x, y = xy[0], xy[1]
                if x not in " ?":
                    has_staged = True
                if y not in " ?":
                    has_unstaged = True
    return has_conflict, has_staged, has_unstaged, has_untracked


def git_status_to_tag(status: str, repo_path: str | None = None) -> tuple[int, str]:
    """Map porcelain output to (color, tag_name).

    Colors:
    - Green: default branch, clean, not behind default.
    - Grey: default branch, clean, behind default.
    - Blue: non-default branch, clean, not behind default.
    - Orange: non-default branch, clean, behind default.
    - Yellow: non-default, unstaged/untracked only, not behind default.
    - Purple: non-default, staged changes only, not behind default.
    - Red: conflict, merge/rebase/cherry-pick/revert, diverged, detached,
      mixed staged+unstaged, uncommitted on default, or local changes while behind.
    """
    lines = [ln.strip() for ln in status.strip().splitlines() if ln.strip()]
    conflict, staged, unstaged, untracked = _aggregate_porcelain(lines)
    dirty = staged or unstaged or untracked

    if conflict:
        return STATUS_MAP["merge_conflict"]

    if repo_path:
        if git_status.repo_in_merge(repo_path):
            return STATUS_MAP["merge_in_progress"]
        if git_status.repo_in_rebase(repo_path):
            return STATUS_MAP["rebase_in_progress"]
        if git_status.repo_in_cherry_pick(repo_path):
            return STATUS_MAP["cherry_pick"]
        if git_status.repo_in_revert(repo_path):
            return STATUS_MAP["revert_in_progress"]
        if git_status.is_diverged_from_origin_default(repo_path):
            return STATUS_MAP["diverged"]

        if git_status.get_current_branch_or_none(repo_path) is None:
            return STATUS_MAP["detached"]

    if staged and unstaged:
        return STATUS_MAP["mixed_staged_unstaged"]

    if repo_path and dirty:
        on_default = git_status.is_on_default_branch(repo_path)
        behind = git_status.is_behind_origin_main(repo_path)
        if on_default:
            return STATUS_MAP["default_dirty"]
        if git_status.is_on_fixed_branch_not_default(repo_path):
            if behind:
                return STATUS_MAP["nondefault_dirty_behind"]
            if staged:
                return STATUS_MAP["nondefault_staged"]
            if unstaged or untracked:
                return STATUS_MAP["nondefault_unstaged"]
        return STATUS_MAP["default_dirty"]

    if not repo_path:
        if dirty:
            if staged and unstaged:
                return STATUS_MAP["mixed_staged_unstaged"]
            if staged:
                return STATUS_MAP["nondefault_staged"]
            if unstaged or untracked:
                return STATUS_MAP["nondefault_unstaged"]
        return STATUS_MAP["up_to_date_default"]

    if git_status.is_on_default_branch(repo_path):
        if git_status.is_behind_origin_main(repo_path):
            return STATUS_MAP["behind_default"]
        return STATUS_MAP["up_to_date_default"]

    if git_status.is_on_fixed_branch_not_default(repo_path):
        if git_status.is_behind_origin_main(repo_path):
            return STATUS_MAP["nondefault_behind"]
        return STATUS_MAP["nondefault_clean_ahead"]

    return STATUS_MAP["detached"]
