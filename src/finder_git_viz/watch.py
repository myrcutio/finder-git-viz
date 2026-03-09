"""Watchdog integration: Observer, schedule paths, run handler."""

from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .config import resolve_global_config
from .handler import on_path_event, refresh_repo
from .scan import find_all_repos


class GitVizHandler(FileSystemEventHandler):
    """Forward file system events to on_path_event."""

    def on_any_event(self, event: FileSystemEvent) -> None:
        src = getattr(event, "src_path", None) or str(event.src_path)
        on_path_event(src)


def watch_paths(paths: list[str]) -> None:
    """Start watching the given paths. Blocks until interrupted."""
    global_config = resolve_global_config()
    for repo in find_all_repos(paths, global_config):
        refresh_repo(repo)

    observer = Observer()
    handler = GitVizHandler()

    for p in paths:
        path = Path(p).resolve()
        if not path.exists():
            continue
        observer.schedule(handler, str(path), recursive=True)

    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
