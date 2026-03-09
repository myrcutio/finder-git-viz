#!/usr/bin/env bash
# Install launchd plist to run finder-git-viz at login.
# Prerequisites: uv tool install finder-git-viz or pipx install finder-git-viz

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLIST_SRC="$PROJECT_ROOT/launchd/com.finder-git-viz.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.finder-git-viz.plist"

if [[ ! -f "$PLIST_SRC" ]]; then
  echo "Error: $PLIST_SRC not found."
  exit 1
fi

# Detect binary path: which, or fallback to ~/.local/bin (uv/pipx default)
BINARY_PATH="$(which finder-git-viz 2>/dev/null)" || true
if [[ -z "$BINARY_PATH" ]]; then
  BINARY_PATH="$HOME/.local/bin/finder-git-viz"
fi
if [[ ! -x "$BINARY_PATH" ]]; then
  echo "Warning: finder-git-viz not found at $BINARY_PATH"
  echo "Install with: uv tool install finder-git-viz  (or pipx install finder-git-viz)"
fi

# Substitute __BINARY_PATH__ and expand ~ to $HOME (launchd doesn't expand ~)
PLIST_CONTENT=$(sed "s|__BINARY_PATH__|$BINARY_PATH|g; s|~|$HOME|g" "$PLIST_SRC")
echo "$PLIST_CONTENT" > "$PLIST_DEST"

# Strip extended attributes (com.apple.provenance etc.) - they can cause
# "Load failed: 5: Input/output error" on Sonoma+
xattr -c "$PLIST_DEST" || echo "Warning: could not clear xattrs (run: xattr -c $PLIST_DEST)"

launchctl unload "$PLIST_DEST"
launchctl load "$PLIST_DEST"
