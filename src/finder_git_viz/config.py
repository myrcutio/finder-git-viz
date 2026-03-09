"""Config resolution with env/project/global precedence."""

import os
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

CONFIG_FILENAME = ".findergitvizconfig"
ENV_CONFIG = "FINDER_GIT_VIZ_CONFIG"
DEFAULT_GLOBS = ["**"]
DEFAULT_SCAN_MODE = "one_level"


def resolve_global_config() -> dict:
    """Resolve global config for scan settings (no repo needed).

    Lookup order:
    1. FINDER_GIT_VIZ_CONFIG env var (path to config file)
    2. ~/.findergitvizconfig

    Returns dict with at least {"scan": {"mode": "one_level", "layouts": []}}.
    """
    if os.environ.get(ENV_CONFIG):
        p = Path(os.environ[ENV_CONFIG])
        if p.is_file():
            return _load_config(p)

    global_config = Path.home() / CONFIG_FILENAME
    if global_config.is_file():
        return _load_config(global_config)

    return {"scan": {"mode": DEFAULT_SCAN_MODE, "layouts": []}}


def resolve_config(repo_path: str) -> dict:
    """Resolve config for a repo.

    Lookup order:
    1. FINDER_GIT_VIZ_CONFIG env var (path to config file)
    2. <repo>/.findergitvizconfig
    3. ~/.findergitvizconfig

    Returns dict with at least {"include": {"globs": [...]}}.
    If no config or globs empty/absent, default globs is ["**"].
    """
    candidates: list[Path] = []

    if os.environ.get(ENV_CONFIG):
        p = Path(os.environ[ENV_CONFIG])
        if p.is_file():
            return _load_config(p)

    repo = Path(repo_path)
    project_config = repo / CONFIG_FILENAME
    if project_config.is_file():
        return _load_config(project_config)

    global_config = Path.home() / CONFIG_FILENAME
    if global_config.is_file():
        return _load_config(global_config)

    return {"include": {"globs": DEFAULT_GLOBS}}


def _load_config(path: Path) -> dict:
    """Load TOML config from path."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    include = data.get("include") or {}
    globs = include.get("globs")
    if not globs:
        globs = DEFAULT_GLOBS

    scan = data.get("scan") or {}
    mode = scan.get("mode") or DEFAULT_SCAN_MODE
    layouts = scan.get("layouts") or []

    return {
        "include": {"globs": globs},
        "scan": {"mode": mode, "layouts": layouts},
    }
