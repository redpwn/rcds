from pathlib import Path
import hashlib
import pathspec  # type: ignore
import docker  # type: ignore

from typing import TYPE_CHECKING, Iterator, Dict, Any, cast, Type

if TYPE_CHECKING:  # pragma: no cover
    from .challenge import Challenge
    from ..project import Project


def get_context_files(root: Path) -> Iterator[Path]:
    """
    Generate a list of all files in the build context of the specified Dockerfile

    :param pathlib.Path root: Path to the containing directory of the Dockerfile to
        analyze
    """
    files: Iterator[Path] = root.rglob("*")
    dockerignore = root / ".dockerignore"
    if dockerignore.exists():
        with dockerignore.open("r") as fd:
            spec = pathspec.PathSpec.from_lines("gitwildmatch", fd)
        files = filter(lambda p: not spec.match_file(p.relative_to(root)), files)
    return filter(lambda p: p.is_file(), files)


def generate_sum(root: Path) -> str:
    """
    Generate a checksum of all files in the build context of the specified directory

    :param pathlib.Path root: Path to the containing directory of the Dockerfile to
        analyze
    """
    h = hashlib.sha256()
    for f in sorted(get_context_files(root), key=lambda f: str(f.relative_to(root))):
        h.update(bytes(f.relative_to(root)))
        with f.open("rb") as fd:
            for chunk in iter(lambda: fd.read(524288), b""):
                h.update(chunk)
    return h.hexdigest()


class Container:
    """
    A single container
    """

    challenge: "Challenge"
    project: "Project"
    name: str
    config: Dict[str, Any]

    IS_BUILDABLE: bool = False

    def __init__(self, *, container_manager: "ContainerManager", name: str) -> None:
        self.challenge = container_manager.challenge
        self.project = self.challenge.project
        self.name = name
        self.config = container_manager.config[self.name]

    def get_full_tag(self) -> str:
        """
        Get the full image tag (e.g. ``k8s.gcr.io/etcd:3.4.3-0``) for this container

        :returns: The image tag
        """
        return self.config["image"]

    def is_built(self) -> bool:
        """
        If the container is buildable (:const:`IS_BUILDABLE` is `True`), this method
        returns whether or not the container is already built (and up-to-date). For
        non-buildable containers, this method always returns `True`.

        :returns: Whether or not the container is built
        """
        return True

    def build(self, force: bool = False) -> None:
        """
        Build the challenge if applicable and necessary.

        For challenges that are not buildable (:const:`IS_BUILDABLE` is False), this
        method is a no-op

        :param bool force: Force a rebuild of this container even if it is up-to-date
        """
        pass


class BuildableContainer(Container):
    """
    A container that is built from source
    """

    root: Path
    dockerfile: str
    buildargs: Dict[str, str]

    IS_BUILDABLE: bool = True

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        build = self.config.get("build", None)
        assert build is not None
        if isinstance(build, str):
            self.root = self.challenge.root / Path(build)
            self.dockerfile = "Dockerfile"
            self.buildargs = dict()
        elif isinstance(build, dict):
            build = cast(Dict[str, Any], build)
            self.root = self.challenge.root / Path(build["context"])
            self.dockerfile = build.get("dockerfile", "Dockerfile")
            self.buildargs = cast(Dict[str, str], build.get("args", dict()))
        self.content_hash = generate_sum(self.root)
        self.image = self.project.get_docker_image(self.name)

    def _build(self) -> None:
        self.project.docker_client.images.build(
            path=str(self.root),
            tag=f"{self.image}:{self.content_hash}",
            dockerfile=self.dockerfile,
            buildargs=self.buildargs,
            pull=True,
            rm=True,
        )

    def get_full_tag(self) -> str:
        return f"{self.image}:{self.content_hash}"

    def is_built(self) -> bool:
        """
        Checks if a container built with a build context with a matching hash exists,
        either locally or remotely.

        :returns: Whether or not the image was found
        """
        try:
            self.project.docker_client.images.get(self.get_full_tag())
            return True
        except docker.errors.ImageNotFound:
            pass  # continue with trying to pull
        try:
            self.project.docker_client.images.pull(self.get_full_tag())
            return True
        except docker.errors.NotFound:
            pass  # continue
        return False

    def build(self, force: bool = False) -> None:
        if force or not self.is_built():
            self._build()


class ContainerManager:
    """
    Object managing all containers defined by a given :class:`rcds.Challenge`
    """

    challenge: "Challenge"
    project: "Project"
    config: Dict[str, Dict[str, Any]]
    containers: Dict[str, Container] = dict()

    def __init__(self, challenge: "Challenge"):
        """
        :param rcds.Challenge challenge: The challenge that this ContainerManager
            belongs to
        """

        self.challenge = challenge
        self.project = self.challenge.project
        self.config = cast(
            Dict[str, Dict[str, Any]], self.challenge.config.get("containers", dict())
        )

        for name in self.config.keys():
            container_config = self.config[name]
            container_constructor: Type[Container]
            if "build" in container_config:
                container_constructor = BuildableContainer
            else:
                container_constructor = Container
            self.containers[name] = container_constructor(
                container_manager=self, name=name
            )
