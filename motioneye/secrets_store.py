"""Persistent secret storage with restrictive file permissions.

Used by `motioneye.settings` to make COOKIE_SECRET stable across
process restarts. Without this, every server boot regenerates the
cookie key, invalidating every active session — bad UX and a
hint that the secret is not persisted (see audit Q10).
"""
import os
import secrets


def get_or_create_secret(path: str) -> str:
    """Return the hex secret stored at `path`, creating it if absent.

    The file is created with mode 0o600 (owner read/write only).
    Existing files are read as-is; if empty, a new secret is written.
    """
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                value = f.read().strip()
            if value:
                return value
        except OSError:
            # Fall through to regenerate if the file is unreadable
            pass

    value = secrets.token_hex(32)
    # O_EXCL would race with concurrent first-startups; use O_CREAT|O_TRUNC
    # with a restrictive mode and accept the rare regeneration on boot races.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, value.encode('utf-8'))
    finally:
        os.close(fd)
    return value
