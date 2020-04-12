from rcds.project import assets
from pathlib import Path
import rcds
from textwrap import dedent
import time
import io

from unittest import mock
import pytest  # type: ignore


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


def test_list_contexts(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    asset_manager.create_context("c1")
    asset_manager.create_context("c2")
    assert set(asset_manager.list_context_names()) == {"c1", "c2"}


def test_create_from_disk(datadir: Path, am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    file1 = datadir / "file1"
    transaction = ctx.transaction()
    transaction.add_file("file1", file1)
    transaction.commit()
    assert "file1" in ctx.ls()
    asset_f1 = ctx.get("file1")
    assert asset_f1.exists()
    assert asset_f1.is_symlink()
    assert asset_f1.resolve() == file1.resolve()


def test_create_from_io(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    contents = b"abcd"
    transaction = ctx.transaction()
    transaction.add("file", time.time(), io.BytesIO(contents))
    transaction.commit()
    assert "file" in ctx.ls()
    asset_file = ctx.get("file")
    with asset_file.open("rb") as fd:
        assert fd.read() == contents


def test_create_from_bytes(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    contents = b"abcd"
    transaction = ctx.transaction()
    transaction.add("file", time.time(), contents)
    transaction.commit()
    assert "file" in ctx.ls()
    asset_file = ctx.get("file")
    with asset_file.open("rb") as fd:
        assert fd.read() == contents


def test_create_from_thunk(am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    contents = b"abcd"
    transaction = ctx.transaction()
    transaction.add("file", time.time(), lambda: contents)
    transaction.commit()
    assert "file" in ctx.ls()
    asset_file = ctx.get("file")
    with asset_file.open("rb") as fd:
        assert fd.read() == contents


def test_transaction_clear(datadir: Path, am_fn: assets.AssetManager) -> None:
    asset_manager = am_fn
    ctx = asset_manager.create_context("challenge")
    transaction = ctx.transaction()
    transaction.add_file("file1", datadir / "file1")
    transaction.commit()
    transaction = ctx.transaction()
    transaction.add_file("file2", datadir / "file2")
    transaction.commit()
    contents = set(ctx.ls())
    assert "file1" not in contents
    assert "file2" in contents


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
