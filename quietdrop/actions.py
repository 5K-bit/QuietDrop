from __future__ import annotations

from pathlib import Path

from .config import Config
from .db import Item, get_item, set_status
from .file_operations import move_item, pending_operations, recover_operations


def mark_reviewed(con, item_id: int) -> Item:
    return _status(con, item_id, "reviewed")


def reject(con, item_id: int) -> Item:
    return _status(con, item_id, "rejected")


def _status(con, item_id, status):
    if get_item(con, item_id) is None:
        raise KeyError(f"item {item_id} not found")
    set_status(con, item_id, status)
    return get_item(con, item_id)


def archive(con, cfg: Config, item_id: int) -> Item:
    item = get_item(con, item_id)
    if item is None:
        raise KeyError(f"item {item_id} not found")
    source = Path(item.path)
    cfg.archive_folder.mkdir(parents=True, exist_ok=True)
    for index in range(10_000):
        name = source.name if index == 0 else f"{source.stem}-{index}{source.suffix}"
        try:
            return move_item(con, item_id, cfg.archive_folder / name, archived=True)
        except FileExistsError:
            continue
    raise RuntimeError("Could not find a free archive filename")


def rename(con, item_id: int, new_name: str) -> Item:
    if not new_name.strip() or new_name in {".", ".."} or any(c in new_name for c in '/\\:'):
        raise ValueError("Enter a filename without path separators")
    item = get_item(con, item_id)
    if item is None:
        raise KeyError(f"item {item_id} not found")
    return move_item(con, item_id, Path(item.path).with_name(new_name))
