"""CLI entrypoint: argparse, --watch, --undo, paths arg, one-shot mode."""

import argparse

from .config import resolve_global_config
from .handler import refresh_repo
from .scan import find_all_repos
from .tags import remove_git_tags
from .watch import watch_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Finder colored tags based on git status"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch paths and update tags on file changes",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Remove all git: tags from repos under the given paths",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Directories to process or watch",
    )
    args = parser.parse_args()

    if args.undo:
        global_config = resolve_global_config()
        for repo in find_all_repos(args.paths, global_config):
            if remove_git_tags(repo):
                print(repo)
    elif args.watch:
        watch_paths(args.paths)
    else:
        global_config = resolve_global_config()
        for repo in find_all_repos(args.paths, global_config):
            refresh_repo(repo)
