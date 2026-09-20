import pytest

from quietdrop.actions import rename, archive
from quietdrop.db import connect, upsert_file, get_item
from quietdrop.file_operations import pending_operations, recover_operations


def setup_item(root):
    source = root / "source.txt"
    source.write_text("source")
    con = connect(root / "queue.db")
    st = source.stat()
    ident = upsert_file(con, path=str(source), filename=source.name, size=st.st_size, mtime=st.st_mtime)
    return con, ident, source


def test_collision_preserves_both_files_and_database(tmp_path):
    con, ident, source = setup_item(tmp_path)
    try:
        target = tmp_path / "target.txt"
        target.write_text("valuable")
        with pytest.raises(FileExistsError):
            rename(con, ident, target.name)
        assert source.read_text() == "source"
        assert target.read_text() == "valuable"
        assert get_item(con, ident).path == str(source)
    finally:
        con.close()


def test_missing_source_does_not_invent_new_path(tmp_path):
    con, ident, source = setup_item(tmp_path)
    try:
        source.unlink()
        with pytest.raises(FileNotFoundError):
            rename(con, ident, "other.txt")
        assert get_item(con, ident).path == str(source)
    finally:
        con.close()


def test_database_failure_keeps_source_and_recovery_copy(tmp_path):
    con, ident, source = setup_item(tmp_path)
    try:
        con.execute("CREATE TRIGGER fail_move BEFORE UPDATE OF path ON items BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        with pytest.raises(Exception, match="test failure"):
            rename(con, ident, "target.txt")
        assert source.read_text() == "source"
        assert (tmp_path / "target.txt").read_text() == "source"
        assert get_item(con, ident).path == str(source)
        assert pending_operations(con)
    finally:
        con.close()


def test_success_completes_journal(tmp_path):
    con, ident, source = setup_item(tmp_path)
    try:
        assert rename(con, ident, "target.txt").filename == "target.txt"
        assert not source.exists()
        assert recover_operations(con) == []
    finally:
        con.close()
