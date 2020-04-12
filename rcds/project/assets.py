from typing import (
    TYPE_CHECKING,
    cast,
    Union,
    BinaryIO,
    Callable,
    Dict,
    Iterable,
    Tuple,
    ByteString,
)
from pathlib import Path
from dataclasses import dataclass
from warnings import warn
import pathlib
import io
import shutil
import os

if TYPE_CHECKING:  # pragma: no cover
    from .project import Project
    import rcds


File = Union[BinaryIO, Path, bytes]
"""
Something that the asset manager can interpret as a file (contents only)

Valid types:

- A :class:`pathlib.Path` object referring to a file that already exists on-disk

- Any :class:`typing.BinaryIO` object that is seekable

- A :class:`typing.ByteString` object containing the contents of the file (internally
  this is converted to a :class:`io.BytesIO`)
"""


def _is_valid_name(name: str):
    return (
        len(pathlib.PurePosixPath(name).parts) == 1
        and len(pathlib.PureWindowsPath(name).parts) == 1
    )


class AssetManagerTransaction:
    """
    A transaction within an :class:`AssetManagerContext`

    This class manages declarative transactional updates to a context, allowing you to
    declare the files that should exist in the context, the last time that file was
    modified, and a callable to run to get the file, should it be out-of-date in the
    cache. The transaction starts in a blank state; without adding anything by calling
    :meth:`add`, :meth:`commit` will clear the context. No actions are performed until
    :meth:`commit` is called.

    This classs is not meant to be constructed directly, use
    :meth:`AssetManagerContext.transaction`
    """

    _asset_manager_context: "AssetManagerContext"
    _is_active: bool

    @dataclass
    class _FileEntry:
        """
        :meta private:
        """

        mtime: float

        # Callable is wrapped in a tuple because otherwise, mypy thinks the field is a
        # class method (related to python/mypy#708)
        get_contents: Tuple[Callable[[], File]]

    _files: Dict[str, _FileEntry]

    def __init__(self, asset_manager_context: "AssetManagerContext"):
        """
        :meta private:
        """
        self._asset_manager_context = asset_manager_context
        self._is_active = True
        self._files = dict()

    def add(
        self, name: str, mtime: float, contents: Union[File, Callable[[], File]]
    ) -> None:
        """
        Add a file to the context

        :param str name: The name of the asset to add
        :param float mtime: The time the asset to add was modified
            (:attr:`os.stat_result.st_mtime`)
        :param contents: The contents of the file - this can either be the contents
            directly as a :const:`File`, or a thunk function that, when calls, returns
            the contents
        :type contents: :const:`File` or :obj:`Callable[[], File]`
        :raises RuntimeError: if the transaction has already been committed
        :raises ValueError: if the asset name is not valid
        """
        if not self._is_active:
            raise RuntimeError("This transaction has already been committed")
        if not _is_valid_name(name):
            raise ValueError(f"Invalid asset name '{name}'")
        get_contents: Callable[[], File]
        if callable(contents):
            get_contents = contents
        else:

            def get_contents() -> File:
                return cast(File, contents)

        self._files[name] = self._FileEntry(mtime=mtime, get_contents=(get_contents,))

    def add_file(self, name: str, file: Path):
        """
        Add an already-existing file on disk to the context

        This wraps :meth:`add`

        :param str name: The name of the asset to add
        :param Path file: The path to the asset on disk
        """
        if not file.is_file():
            raise ValueError(f"Provided file does not exist: '{str(file)}'")
        self.add(name, file.stat().st_mtime, lambda: file)

    def _create(self, fpath: Path, fentry: _FileEntry) -> None:
        """
        Create / overwrite the asset in the cache

        :meta private:
        """
        contents = fentry.get_contents[0]()
        if isinstance(contents, Path):
            if not contents.is_file():
                raise ValueError(f"Provided file does not exist: '{str(contents)}'")
            fpath.symlink_to(contents)
        if isinstance(contents, ByteString):
            contents = io.BytesIO(contents)
        if isinstance(contents, io.IOBase):
            with fpath.open("wb") as ofd:
                shutil.copyfileobj(contents, ofd)
        os.utime(fpath, (fentry.mtime, fentry.mtime))

    def commit(self) -> None:
        """
        Commit the transaction.

        This transaction can no longer be used after :meth:`commit` is called.
        """
        self._is_active = False
        self._asset_manager_context._is_transaction_active = False
        files_to_delete = set(self._asset_manager_context._root.iterdir())
        print(files_to_delete)
        for name, file_entry in self._files.items():
            fpath = self._asset_manager_context._root / name
            try:
                # TODO: maybe resolve all paths when checking what files to delete?
                files_to_delete.remove(fpath)
            except KeyError:
                pass
            if fpath.exists() and not fpath.is_file():
                raise RuntimeError(f"Unexpected item found in cache: '{str(fpath)}'")
            if fpath.exists():
                cache_mtime = self._asset_manager_context.get_mtime(name)
                if not file_entry.mtime > cache_mtime:
                    continue
            self._create(fpath, file_entry)
        print(files_to_delete)
        for file in files_to_delete:
            if not file.is_file():
                raise RuntimeError(f"Unexpected item found in cache: '{str(fpath)}'")
            file.unlink()


class AssetManagerContext:
    """
    A subcontext within an :class:`AssetManager`

    Represents a namespace within the :class:`AssetManager`, essentially a
    subdirectory. The context holds assets for a challenge with the same id

    This class is not meant to be constructed directly, use
    :meth:`AssetManager.create_context`
    """

    _asset_manager: "AssetManager"
    _name: str
    _root: Path

    _is_transaction_active: bool

    def __init__(self, asset_manager: "AssetManager", name: str):
        """
        :meta private:
        """
        self._asset_manager = asset_manager
        self._name = name
        self._is_transaction_active = False
        self._root = self._asset_manager.root / name
        self._root.mkdir(parents=True, exist_ok=True)

    def transaction(self) -> AssetManagerTransaction:
        """
        Create a :class:`AssetManagerTransaction`.

        Only one transaction can be created at a time.

        :returns: The transaction
        :raises RuntimeError: when attempting to create a transaction while one already
            exists
        """
        # TODO: better locking mechanism?
        if self._is_transaction_active:
            raise RuntimeError(
                "Attempted to create transaction while one is already in progress"
            )
        self._is_transaction_active = True
        return AssetManagerTransaction(self)

    def ls(self) -> Iterable[str]:
        """
        List all files within this context

        :returns: The list of asset names
        """
        for f in self._root.iterdir():
            if not f.is_file():
                raise RuntimeError(f"Unexpected item found in cache: '{str(f)}'")
            yield f.name

    def clear(self) -> None:
        """
        Clear all files in this context
        """
        for f in self._root.iterdir():
            if not f.is_file():
                warn(
                    RuntimeWarning(
                        f"Unexpected item found in cache: '{str(f)}'; removing..."
                    )
                )
                if f.is_dir():
                    shutil.rmtree(f)
                    continue
            f.unlink()

    def get(self, name: str) -> Path:
        """
        Retrieves the asset

        :param str name: The name of the asset
        :returns: The asset
        """
        if not _is_valid_name(name):
            raise ValueError(f"Invalid asset name '{name}'")
        return self._root / name

    def get_mtime(self, name: str) -> float:
        """
        Retrieves the time an asset was modified

        :param str name: The name of the asset
        :returns: The time the asset was modified (:attr`os.stat_result.st_mtime`)
        """
        return self.get(name).stat().st_mtime


class AssetManager:
    """
    Class for managing assets from challenges that are provided to competitors

    This class manages all assets under a given project.
    """

    project: "Project"
    root: Path

    def __init__(self, project: "rcds.Project"):
        self.project = project
        self.root = self.project.root / ".rcds-cache" / "assets"
        self.root.mkdir(parents=True, exist_ok=True)

    def create_context(self, name: str) -> AssetManagerContext:
        """
        Create a subcontext within the :class:`AssetManager`

        :param str name: The name of the context (challenge id)
        :raises ValueError: if the context name is not valid
        """
        if not _is_valid_name(name):
            raise ValueError(f"Invalid context name '{name}'")
        return AssetManagerContext(self, name)

    def list_context_names(self) -> Iterable[str]:
        """
        List the names of all subcontexts within this :class:`AssetManager`

        :returns: The contexts' names. Call :meth:`create_context` on a name to obtain a
            :class:`AssetManagerContext` object
        """
        for d in self.root.iterdir():
            if not d.is_dir():
                raise RuntimeError(f"Unexpected item found in cache: '{str(d)}'")
            yield d.name
