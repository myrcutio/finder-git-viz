# finder-git-viz

Finder colored tags based on git status. Monitors directories and updates Finder tags to reflect git state (clean, uncommitted changes, untracked, etc.).

## Installation

```bash
uv tool install finder-git-viz
# or
pipx install finder-git-viz
```

## Usage

- **One-shot** (update tags once and exit):
  ```bash
  finder-git-viz /path/to/projects
  ```

- **Watch mode** (monitor and update on file changes):
  ```bash
  finder-git-viz --watch /path/to/projects
  ```

- **Undo** (remove all `git:` tags from repos):
  ```bash
  finder-git-viz --undo /path/to/projects
  ```
  Preserves other tags; only removes tags starting with `git:`.

## Config

Config file: `~/.findergitvizconfig` or `<repo>/.findergitvizconfig`. Set `FINDER_GIT_VIZ_CONFIG` to override.

**Include globs** — which files trigger a refresh (default: `["**"]`):
```toml
[include]
globs = ["**"]
```

**Scan mode** — how repos are discovered under watched paths:
```toml
[scan]
# strict | one_level | greedy | layout
mode = "one_level"
layouts = [
  { path_name = "all_projects_folder", repo_pattern = "subprojects_folder/*/*/.git" }
]
```

See `findergitvizconfig.example` for a full example.

## launchd (run at login)

To run the watcher at login:

1. Run `./scripts/install-launchd.sh` to copy the plist to `~/Library/LaunchAgents/` (substitutes your binary path automatically).
2. Edit the installed plist to change watched paths (default: `~/projects`).
3. Load: `launchctl load ~/Library/LaunchAgents/com.finder-git-viz.plist`
4. Unload: `launchctl unload ~/Library/LaunchAgents/com.finder-git-viz.plist`

Logs: `/tmp/finder-git-viz.log` and `/tmp/finder-git-viz.err`.

## macOS only

Requires macOS for Finder tags and xattr.
