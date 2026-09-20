"""Recoverable, exclusive file moves. Files are retained until the DB commits."""
from __future__ import annotations

import hashlib
import os
import shutil
import stat
import time
import uuid
from pathlib import Path

from .db import get_item


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _journal(con) -> None:
    con.execute("""CREATE TABLE IF NOT EXISTS file_operations (
        id TEXT PRIMARY KEY, item_id INTEGER NOT NULL, source TEXT NOT NULL,
        destination TEXT NOT NULL, digest TEXT, state TEXT NOT NULL,
        created_at REAL NOT NULL, error TEXT)""")
    con.commit()


def pending_operations(con) -> list[dict]:
    _journal(con)
    return [dict(row) for row in con.execute(
        "SELECT * FROM file_operations WHERE state != 'complete' ORDER BY created_at"
    )]


def recover_operations(con) -> list[dict]:
    """Finish committed moves only when their recorded contents still match."""
    _journal(con)
    for row in pending_operations(con):
        src, dest = Path(row["source"]), Path(row["destination"])
        item = get_item(con, row["item_id"])
        try:
            committed = item is not None and item.path == str(dest)
            if not committed:
                # Leave both files available for review after an interrupted copy.
                continue
            if not dest.is_file() or dest.is_symlink() or _digest(dest) != row["digest"]:
                continue
            if src.exists():
                if src.is_symlink() or _digest(src) != row["digest"]:
                    continue
                src.unlink()
            con.execute("UPDATE file_operations SET state='complete',error=NULL WHERE id=?", (row["id"],))
            con.commit()
        except OSError as exc:
            con.execute("UPDATE file_operations SET error=? WHERE id=?", (str(exc), row["id"]))
            con.commit()
    return pending_operations(con)


def move_item(con, item_id: int, destination: Path, *, archived: bool = False):
    item = get_item(con, item_id)
    if item is None:
        raise KeyError(f"item {item_id} not found")
    source = Path(item.path)
    if source == destination:
        return item
    if source.is_symlink() or not stat.S_ISREG(source.stat().st_mode):
        raise ValueError("Only regular files can be moved")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Destination already exists: {destination.name}")
    _journal(con)
    operation_id = uuid.uuid4().hex
    con.execute("INSERT INTO file_operations VALUES (?,?,?,?,?,'prepared',?,NULL)",
                (operation_id, item_id, str(source), str(destination), None, time.time()))
    con.commit()
    before = source.stat()
    try:
        # Exclusive creation protects against a competing move choosing this name.
        with source.open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        digest = _digest(destination)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or _digest(source) != digest:
            raise RuntimeError("Source changed during copy; both files retained for review")
        shutil.copystat(source, destination)
        with con:
            result = con.execute(
                "UPDATE items SET path=?,filename=?,status=?,archived_at=COALESCE(archived_at,?) WHERE id=? AND path=?",
                (str(destination), destination.name, "archived" if archived else item.status,
                 time.time() if archived else None, item_id, str(source)),
            )
            if result.rowcount != 1:
                raise RuntimeError("Item changed during move")
            con.execute("UPDATE file_operations SET state='committed',digest=? WHERE id=?", (digest, operation_id))
    except Exception as exc:
        con.rollback()
        con.execute("UPDATE file_operations SET error=? WHERE id=?", (str(exc), operation_id))
        con.commit()
        raise
    # A cleanup failure does not undo the committed destination; the journal
    # allows the next recovery pass to finish without deleting changed files.
    recover_operations(con)
    return get_item(con, item_id)
