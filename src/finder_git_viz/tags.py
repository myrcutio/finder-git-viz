"""Finder tag operations via xattr."""

import plistlib
import re
import subprocess

TAG_XATTR = "com.apple.metadata:_kMDItemUserTags"
GIT_TAG_PREFIX = "git:"


def _read_finder_tags(path: str) -> list[str]:
    """Read current Finder tags from path. Returns list of 'tagname\\nCOLOR' strings."""
    result = subprocess.run(
        ["xattr", "-p", TAG_XATTR, path],
        capture_output=True,
        text=False,
    )
    if result.returncode != 0:
        return []
    data = result.stdout
    try:
        tags = plistlib.loads(data)
    except plistlib.InvalidFileException:
        # xattr output may include DOCTYPE which plistlib rejects; extract plist only
        match = re.search(rb"<plist[^>]*>.*</plist>", data, re.DOTALL)
        if match:
            try:
                tags = plistlib.loads(match.group(0))
            except Exception:
                return []
        else:
            return []
    except Exception:
        return []
    return tags if isinstance(tags, list) else []


def remove_git_tags(path: str) -> bool:
    """Remove all tags starting with 'git:' from path. Preserve other tags.

    Returns True if any tags were removed or changed.
    """
    tags = _read_finder_tags(path)
    if not tags:
        return False
    remaining = [t for t in tags if not t.split("\n")[0].startswith(GIT_TAG_PREFIX)]
    if len(remaining) == len(tags):
        return False
    if not remaining:
        subprocess.run(
            ["xattr", "-d", TAG_XATTR, path],
            capture_output=True,
            check=False,
        )
        return True
    plist = plistlib.dumps(remaining, fmt=plistlib.FMT_BINARY)
    subprocess.run(
        ["xattr", "-w", "-x", TAG_XATTR, plist.hex(), path],
        capture_output=True,
        check=True,
    )
    return True


def set_finder_tag(path: str, tag_name: str, color: int) -> None:
    """Set a Finder tag with color on the given path.

    Tags are stored in com.apple.metadata:_kMDItemUserTags as a plist array.
    Each string is "tagname\\nCOLOR" where COLOR is 0-7:
    0=none, 1=grey, 2=green, 3=purple, 4=blue, 5=yellow, 6=red, 7=orange.

    Note: This overwrites existing tags. Use read_finder_tags + merge if preserving.
    """
    plist = (
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        "<plist version=\"1.0\"><array><string>"
        f"{tag_name}\n{color}"
        "</string></array></plist>"
    )
    subprocess.run(
        ["xattr", "-w", "com.apple.metadata:_kMDItemUserTags", plist, path],
        check=True,
        capture_output=True,
    )
