from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from ..util import SUPPORTED_EXTENSIONS, deep_merge, find_files
from .config import ConfigLoader

if TYPE_CHECKING:  # pragma: no cover
    from ..project import Project
    import rcds


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

    def __init__(self, project: "Project", root: Path, config: dict):
        self.project = project
        self.root = root
        self.config = config
        self.context = dict()

    def get_relative_path(self) -> Path:
        """
        Utiity function to get this challenge's path relative to the project root
        """
        return self.root.relative_to(self.project.root)

    def render_description(self) -> str:
        """
        Render the challenge's description template to a string
        """
        return self.project.jinja_env.from_string(self.config["description"]).render(
            deep_merge(dict(), {"challenge": self.config}, self.context)
        )
