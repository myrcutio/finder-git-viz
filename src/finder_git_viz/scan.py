"""Startup scan: find .git dirs in watched paths and return repo roots."""

from pathlib import Path


def _repos_from_pattern(base_path: Path, repo_pattern: str) -> list[str]:
    """Find repo roots matching repo_pattern under base_path.

    repo_pattern is a glob like "projects/*/*/.git" relative to base_path.
    Returns parent dirs of each .git found (the repo roots).
    """
    repos: list[str] = []
    for git_dir in base_path.glob(repo_pattern):
        if git_dir.is_dir():
            repos.append(str(git_dir.parent))
    return repos


def _repos_one_level(path: Path) -> list[str]:
    """Direct children only: path/*/.git."""
    repos: list[str] = []
    for child in path.iterdir():
        if child.is_dir() and (child / ".git").is_dir():
            repos.append(str(child))
    return repos


def find_repos_in_path(watched_path: str, global_config: dict) -> list[str]:
    """Find repo roots under a watched path.

    Modes (from config scan.mode):
    - strict:  only watched_path if it has .git
    - one_level: path/*/.git (direct children)
    - greedy:   path/**/.git (all descendants)
    - layout:   use path_name + repo_pattern for matching paths; else one_level
    """
    path = Path(watched_path).resolve()
    if not path.exists() or not path.is_dir():
        return []

    scan_config = global_config.get("scan") or {}
    mode = scan_config.get("mode") or "one_level"
    layouts = scan_config.get("layouts") or []

    if mode == "strict":
        if (path / ".git").is_dir():
            return [str(path)]
        return []

    if mode == "greedy":
        repos: list[str] = []
        for git_dir in path.rglob(".git"):
            if git_dir.is_dir():
                repos.append(str(git_dir.parent))
        return repos

    if mode == "layout":
        result: list[str] = []
        # Check if path itself matches a layout
        for layout in layouts:
            if isinstance(layout, dict) and layout.get("path_name") == path.name:
                pattern = layout.get("repo_pattern")
                if pattern:
                    return _repos_from_pattern(path, pattern)
        # Path doesn't match; check each direct child
        for child in path.iterdir():
            if not child.is_dir():
                continue
            matched = False
            for layout in layouts:
                if isinstance(layout, dict) and layout.get("path_name") == child.name:
                    pattern = layout.get("repo_pattern")
                    if pattern:
                        result.extend(_repos_from_pattern(child, pattern))
                        matched = True
                        break
            if not matched:
                if (child / ".git").is_dir():
                    result.append(str(child))
                else:
                    result.extend(_repos_one_level(child))
        return result

    # one_level (default): path itself if repo, plus direct children
    repos = []
    if (path / ".git").is_dir():
        repos.append(str(path))
    repos.extend(_repos_one_level(path))
    return repos


def find_all_repos(watched_paths: list[str], global_config: dict) -> list[str]:
    """Find all repo roots across watched paths. Deduplicated."""
    seen: set[str] = set()
    result: list[str] = []
    for p in watched_paths:
        for repo in find_repos_in_path(p, global_config):
            resolved = str(Path(repo).resolve())
            if resolved not in seen:
                seen.add(resolved)
                result.append(resolved)
    return result
