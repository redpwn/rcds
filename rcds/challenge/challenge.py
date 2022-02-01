import re
from pathlib import Path
import os
import tempfile
import zipfile
from typing import TYPE_CHECKING, Any, Callable, Dict, cast

import pathspec

from ..util import SUPPORTED_EXTENSIONS, deep_merge, find_files
from .config import ConfigLoader

if TYPE_CHECKING:
    import rcds

    from ..project import Project
    from ..project.assets import AssetManagerContext, AssetManagerTransaction


def _strip_scheme(url: str) -> str:
    return re.sub(r".*?://", "", url)


class ChallengeLoader:
    """
    Class for loading a :class:`Challenge` within the context of a
    :class:`rcds.Project`
    """

    project: "Project"
    _config_loader: ConfigLoader

    def __init__(self, project: "rcds.Project"):
        self.project = project
        self._config_loader = ConfigLoader(self.project)

    def load(self, root: Path):
        """
        Load a challenge by path

        The challenge must be within the project associated with this loader.

        :param pathlib.Path root: Path to challenge root
        """
        try:
            cfg_file = find_files(
                ["challenge"], SUPPORTED_EXTENSIONS, path=root, recurse=False
            )["challenge"]
        except KeyError:
            raise ValueError(f"No config file found at '{root}'")
        config = self._config_loader.load_config(cfg_file)
        return Challenge(self.project, root, config)


class Challenge:
    """
    A challenge within a given :class:`rcds.Project`

    This class is not meant to be constructed directly, use a :class:`ChallengeLoader`
    to load a challenge.
    """

    project: "Project"
    root: Path
    config: Dict[str, Any]
    context: Dict[str, Any]  # overrides to Jinja context
    _asset_manager_context: "AssetManagerContext"
    _asset_sources: Dict[str, Callable[[Dict[str, Any]], Path]]

    def __init__(self, project: "Project", root: Path, config: dict):
        self.project = project
        self.root = root
        self.config = config
        self.context = dict()
        self._asset_manager_context = self.project.asset_manager.create_context(
            self.config["id"]
        )
        self._asset_sources = {}

        self.register_asset_source("file", self._add_file_asset)
        self.register_asset_source("zip", self._add_zip_asset)

    # def _add_static_assets(self, transaction: "AssetManagerTransaction") -> None:
    #     if "provide" not in self.config:
    #         return
    #     for provide in self.config["provide"]:
    #         if isinstance(provide, str):
    #             path = self.root / Path(provide)
    #             name = path.name
    #         else:
    #             path = self.root / Path(provide["file"])
    #             name = provide["as"]
    #         transaction.add_file(name, path)

    def _add_file_asset(self, spec: Dict[str, Any]) -> Path:
        path = self.root / Path(spec["file"])
        return path

    def _add_zip_asset(self, spec: Dict[str, Any]) -> Path:
        exclude: pathspec.PathSpec = None
        if "exclude" in spec:
            exclude = pathspec.PathSpec.from_lines("gitwildmatch", spec["exclude"])
        fd, fn = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        with zipfile.ZipFile(fn, 'w') as zf:
            def add(path: Path):
                if exclude is not None and exclude.match_file(path.relative_to(self.root)):
                    return
                if path.is_file():
                    print(path, path.relative_to(self.root))
                    zf.write(path, path.relative_to(self.root), zipfile.ZIP_DEFLATED)
                elif path.is_dir():
                    zf.write(path, path.relative_to(self.root), zipfile.ZIP_STORED)
                    for nm in path.iterdir():
                        add(nm)

            for glob in spec["files"]:
                for path in self.root.glob(glob):
                    add(path)

        return Path(fn)

    def register_asset_source(
        self, kind: str, do_add: Callable[["AssetManagerTransaction"], None]
    ) -> None:
        """
        Register a function to add assets to the transaction for this challenge.
        """
        self._asset_sources[kind] = do_add

    def create_transaction(self) -> "AssetManagerTransaction":
        """
        Get a transaction to update this challenge's assets
        """
        transaction = self._asset_manager_context.transaction()
        if "provide" not in self.config:
            return transaction
        for provide in self.config["provide"]:
            if isinstance(provide, str):
                path = self.root / Path(provide)
                name = path.name
            else:
                path = self._asset_sources[provide["kind"]](provide["spec"])
                name = provide["as"]
            transaction.add_file(name, path)
        return transaction

    def get_asset_manager_context(self) -> "AssetManagerContext":
        return self._asset_manager_context

    def get_relative_path(self) -> Path:
        """
        Utiity function to get this challenge's path relative to the project root
        """
        return self.root.relative_to(self.project.root)

    def get_context_shortcuts(self) -> Dict[str, Any]:
        shortcuts: Dict[str, Any] = dict()

        if (
            "expose" in self.config
            and len(self.config["expose"]) == 1
            and len(next(iter(cast(Dict[str, list], self.config["expose"]).values())))
            == 1
        ):
            # One container exposed; we can define expose shortcuts
            expose_cfg = cast(
                Dict[str, Any], next(iter(self.config["expose"].values()))[0]
            )
            shortcuts["host"] = expose_cfg.get("http", expose_cfg.get("host", None))
            has_url = False
            if "tcp" in expose_cfg:
                shortcuts["port"] = expose_cfg["tcp"]
                shortcuts["nc"] = f"nc {shortcuts['host']} {shortcuts['port']}"
                shortcuts["url"] = f"http://{shortcuts['host']}:{shortcuts['port']}"
                has_url = True
            if "http" in expose_cfg:
                shortcuts["url"] = f"https://{shortcuts['host']}"
                has_url = True
            if has_url:
                shortcuts[
                    "link"
                ] = f"[{_strip_scheme(shortcuts['url'])}]({shortcuts['url']})"

        return shortcuts

    def render_description(self) -> str:
        """
        Render the challenge's description template to a string
        """

        return self.project.jinja_env.from_string(self.config["description"]).render(
            deep_merge(
                dict(),
                {"challenge": self.config},
                self.get_context_shortcuts(),
                self.context,
            )
        )
