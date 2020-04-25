import io
import time
from pathlib import Path
from textwrap import dedent
from unittest import mock

import pytest  # type: ignore

import rcds
from rcds.project import assets


def _create_project(path: Path) -> None:
    (path / "rcds.yml").write_text(
        dedent(
            """\
            """
        )
    )


@pytest.fixture(scope="function")
def am_fn(tmp_path: Path) -> assets.AssetManager:
    """
    Function-scoped AssetManager
    """
    root = tmp_path
    _create_project(root)
    project = rcds.Project(root)
    return assets.AssetManager(project)


def test_name_validation() -> None:
    assert assets._is_valid_name("valid")
    assert not assets._is_valid_name("../directory_traversal")
    assert not assets._is_valid_name(r"..\win_dir_traversal")
    assert not assets._is_valid_name("/absolute")
    assert not assets._is_valid_name(r"C:\win_absolute")


def test_list_contexts(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    asset_manager.create_context("c1")
    asset_manager.create_context("c2")
    assert set(asset_manager.list_context_names()) == {"c1", "c2"}


def test_get_nonexistent(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    with pytest.raises(FileNotFoundError) as errinfo:
        ctx.get("nonexistent")
    assert str(errinfo.value) == "Asset not found: 'nonexistent'"


def test_create_from_disk(datadir: Path, am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    file1 = datadir / "file1"
    transaction = ctx.transaction()
    transaction.add_file("file1", file1)
    transaction.commit()
    assert set(ctx.ls()) == {"file1"}
    asset_f1 = ctx.get("file1")
    assert asset_f1.exists()
    assert asset_f1.is_symlink()
    assert asset_f1.resolve() == file1.resolve()
    ctx2 = asset_manager.create_context("challenge")
    assert set(ctx2.ls()) == {"file1"}


def test_create_from_io(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    contents = b"abcd"
    transaction = ctx.transaction()
    transaction.add("file", time.time(), io.BytesIO(contents))
    transaction.commit()
    assert set(ctx.ls()) == {"file"}
    asset_file = ctx.get("file")
    with asset_file.open("rb") as fd:
        assert fd.read() == contents
    ctx2 = asset_manager.create_context("challenge")
    assert set(ctx2.ls()) == {"file"}


def test_create_from_bytes(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    contents = b"abcd"
    transaction = ctx.transaction()
    transaction.add("file", time.time(), contents)
    transaction.commit()
    assert set(ctx.ls()) == {"file"}
    asset_file = ctx.get("file")
    with asset_file.open("rb") as fd:
        assert fd.read() == contents
    ctx2 = asset_manager.create_context("challenge")
    assert set(ctx2.ls()) == {"file"}


def test_create_from_thunk(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    contents = b"abcd"
    transaction = ctx.transaction()
    transaction.add("file", time.time(), lambda: contents)
    transaction.commit()
    assert set(ctx.ls()) == {"file"}
    asset_file = ctx.get("file")
    with asset_file.open("rb") as fd:
        assert fd.read() == contents
    ctx2 = asset_manager.create_context("challenge")
    assert set(ctx2.ls()) == {"file"}


def test_create_from_multiple_literals(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    contents1 = b"abcd"
    contents2 = b"wxyz"
    transaction = ctx.transaction()
    transaction.add("file1", time.time(), contents1)
    transaction.add("file2", time.time(), contents2)
    transaction.commit()
    assert set(ctx.ls()) == {"file1", "file2"}
    with ctx.get("file1").open("rb") as fd:
        assert fd.read() == contents1
    with ctx.get("file2").open("rb") as fd:
        assert fd.read() == contents2
    ctx2 = asset_manager.create_context("challenge")
    assert set(ctx2.ls()) == {"file1", "file2"}


def test_transaction_clear(datadir: Path, am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    transaction.add_file("file1", datadir / "file1")
    transaction.commit()
    transaction = ctx.transaction()
    transaction.add_file("file2", datadir / "file2")
    transaction.commit()
    assert set(ctx.ls()) == {"file2"}
    ctx2 = asset_manager.create_context("challenge")
    assert set(ctx2.ls()) == {"file2"}


def test_updates_when_newer(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")

    contents = b"abcd"

    transaction = ctx.transaction()
    transaction.add("file", 1, contents)
    transaction.commit()

    get_contents = mock.Mock(return_value=contents)
    transaction = ctx.transaction()
    transaction.add("file", 2, get_contents)
    transaction.commit()

    get_contents.assert_called()


def test_does_not_update_when_older(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")

    contents = b"abcd"

    transaction = ctx.transaction()
    transaction.add("file", 2, contents)
    transaction.commit()

    get_contents = mock.Mock(return_value=contents)
    transaction = ctx.transaction()
    transaction.add("file", 1, get_contents)
    transaction.commit()

    get_contents.assert_not_called()


def test_context_clear(datadir: Path, am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    transaction.add_file("file1", datadir / "file1")
    transaction.add_file("file2", datadir / "file2")
    transaction.add("file3", time.time(), b"abcd")
    transaction.commit()
    assert len(list(ctx.ls())) != 0
    ctx.clear()
    assert len(list(ctx.ls())) == 0
    ctx2 = asset_manager.create_context("challenge")
    assert len(list(ctx2.ls())) == 0


def test_disallow_concurrent_transaction(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    ctx.transaction()
    with pytest.raises(RuntimeError) as errinfo:
        ctx.transaction()
    assert (
        str(errinfo.value) == "Attempted to create transaction while one is already "
        "in progress"
    )


def test_disallow_add_after_commit(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    transaction.commit()
    with pytest.raises(RuntimeError) as errinfo:
        transaction.add("file", time.time(), b"abcd")
    assert str(errinfo.value) == "This transaction has already been committed"


def test_disallow_invalid_file_name(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    with pytest.raises(ValueError) as errinfo:
        transaction.add("bad/../name", time.time(), b"abcd")
    assert str(errinfo.value) == "Invalid asset name 'bad/../name'"
    transaction.commit()
    with pytest.raises(ValueError) as errinfo:
        ctx.get("bad/../name")
    assert str(errinfo.value) == "Invalid asset name 'bad/../name'"


def test_disallow_invalid_challenge_name(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    with pytest.raises(ValueError) as errinfo:
        asset_manager.create_context("bad/../name")
    assert str(errinfo.value) == "Invalid context name 'bad/../name'"


def test_disallow_nonexistent_files_add_file(
    datadir: Path, am_fn: assets.AssetManager
) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    with pytest.raises(ValueError) as errinfo:
        transaction.add_file("file", datadir / "nonexistent")
    assert "Provided file does not exist: " in str(errinfo.value)


def test_disallow_directories_files_add_file(
    datadir: Path, am_fn: assets.AssetManager
) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    with pytest.raises(ValueError) as errinfo:
        transaction.add_file("file", datadir / "dir")
    assert "Provided file does not exist: " in str(errinfo.value)


def test_disallow_nonexistent_files_add(
    datadir: Path, am_fn: assets.AssetManager
) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    transaction.add("file", time.time(), datadir / "nonexistent")
    with pytest.raises(ValueError) as errinfo:
        transaction.commit()
    assert "Provided file does not exist: " in str(errinfo.value)


def test_disallow_directories_files_add(
    datadir: Path, am_fn: assets.AssetManager
) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    transaction.add("file", time.time(), datadir / "dir")
    with pytest.raises(ValueError) as errinfo:
        transaction.commit()
    assert "Provided file does not exist: " in str(errinfo.value)


class TestCacheErrorRecovery:
    def test_deleted_asset(self, datadir: Path, am_fn: assets.AssetManager) -> None:
        asset_manager = am_fn
        ctx = asset_manager.create_context("challenge")
        transaction = ctx.transaction()
        transaction.add_file("file1", datadir / "file1")
        transaction.commit()
        (ctx._root / "files" / "file1").unlink()
        with pytest.raises(RuntimeError) as errinfo:
            ctx.sync(check=True)
        assert "Cache item missing: " in str(errinfo.value)

    def test_extra_file(self, datadir: Path, am_fn: assets.AssetManager) -> None:
        asset_manager = am_fn
        ctx = asset_manager.create_context("challenge")
        file1 = ctx._root / "files" / "file1"
        with file1.open("w") as fd:
            fd.write("abcd")
        with pytest.warns(RuntimeWarning) as record:
            ctx.sync(check=True)
        assert len(record) == 1
        assert "Unexpected item found in cache: " in str(record[0].message.args[0])
        assert not file1.exists()

    def test_extra_dir(self, datadir: Path, am_fn: assets.AssetManager) -> None:
        asset_manager = am_fn
        ctx = asset_manager.create_context("challenge")
        dir1 = ctx._root / "files" / "dir1"
        dir1.mkdir()
        with pytest.warns(RuntimeWarning) as record:
            ctx.sync(check=True)
        assert len(record) == 1
        assert "Unexpected item found in cache: " in str(record[0].message.args[0])
        assert not dir1.exists()


class TestInternals:
    def test_add_remove(self, am_fn: assets.AssetManager) -> None:
        asset_manager = am_fn
        ctx = asset_manager.create_context("challenge")
        ctx._add("file")
        assert "file" in ctx.ls()
        ctx._rm("file")
        assert "file" not in ctx.ls()

    def test_add_existing_raises(self, am_fn: assets.AssetManager) -> None:
        asset_manager = am_fn
        ctx = asset_manager.create_context("challenge")
        ctx._add("file", force=True)
        with pytest.raises(FileExistsError) as errinfo:
            ctx._add("file", force=False)
        assert str(errinfo.value) == "Asset already exists: 'file'"

    def test_force_add_existing(self, am_fn: assets.AssetManager) -> None:
        asset_manager = am_fn
        ctx = asset_manager.create_context("challenge")
        ctx._add("file", force=True)
        ctx._add("file", force=True)
        assert "file" in ctx.ls()

    def test_remove_nonexistent_raises(self, am_fn: assets.AssetManager) -> None:
        asset_manager = am_fn
        ctx = asset_manager.create_context("challenge")
        with pytest.raises(FileNotFoundError) as errinfo:
            ctx._rm("file", force=False)
        assert str(errinfo.value) == "Asset not found: 'file'"

    def test_force_remove_nonexistent(self, am_fn: assets.AssetManager) -> None:
        asset_manager = am_fn
        ctx = asset_manager.create_context("challenge")
        ctx._rm("file", force=True)
        assert "file" not in ctx.ls()
