from pathlib import Path, PurePosixPath
from typing import Any, Dict, Optional

import docker  # type: ignore

from rcds.util import SUPPORTED_EXTENSIONS, find_files, load_any

from ..challenge import Challenge, ChallengeLoader


class Project:
    """
    An rCDS project; the context that all actions are done within
    """

    root: Path
    config: dict
    challenges: Dict[Path, Challenge]
    challenge_loader: ChallengeLoader
    docker_client: Any

    def __init__(
        self, root: Path, docker_client: Optional[docker.client.DockerClient] = None
    ):
        """
        Create a project
        """
        root = root.resolve()
        try:
            cfg_file = find_files(
                ["rcds"], SUPPORTED_EXTENSIONS, path=root, recurse=False
            )["rcds"]
        except KeyError:
            raise ValueError(f"No config file found at '{root}'")
        self.root = root
        self.config = load_any(cfg_file)
        self.challenge_loader = ChallengeLoader(self)
        if docker_client is not None:
            self.docker_client = docker_client
        else:
            self.docker_client = docker.from_env()

    def load_all_challenges(self) -> None:
        for ext in SUPPORTED_EXTENSIONS:
            for chall_file in self.root.rglob(f"challenge.{ext}"):
                path = chall_file.parent
                self.challenges[
                    path.relative_to(self.root)
                ] = self.challenge_loader.load(path)

    def get_challenge(self, relPath: Path) -> Challenge:
        return self.challenges[relPath]

    def get_docker_image(self, image: str) -> str:
        try:
            image = self.config["docker"]["image-prefix"] + image
        except KeyError:
            pass
        # FIXME: better implementation than abusing PosixPath?
        return str(PurePosixPath(self.config["docker"]["registry"]) / image)
