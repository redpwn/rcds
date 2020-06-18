import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Dict, Iterator, Type, cast

import docker  # type: ignore
import pathspec  # type: ignore

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

    manager: "ContainerManager"
    challenge: "Challenge"
    project: "Project"
    name: str
    config: Dict[str, Any]

    IS_BUILDABLE: bool = False

    def __init__(self, *, container_manager: "ContainerManager", name: str) -> None:
        self.manager = container_manager
        self.challenge = self.manager.challenge
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
        self.image = self.manager.get_docker_image(self)

    def _build(self) -> None:
        self.project.docker_client.images.build(
            path=str(self.root),
            tag=f"{self.image}:{self.content_hash}",
            dockerfile=self.dockerfile,
            buildargs=self.buildargs,
            pull=True,
            rm=True,
        )
        self.project.docker_client.images.push(
            self.image, tag=self.content_hash, auth_config=self.manager._auth_config
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
            self.project.docker_client.images.get_registry_data(
                self.get_full_tag(), auth_config=self.manager._auth_config
            )
            return True
        except docker.errors.NotFound:
            pass  # continue
        return False

    def build(self, force: bool = False) -> None:
        if force or not self.is_built():
            self._build()


class _AuthCfgCache:
    _cache: Dict[str, Dict[str, str]] = dict()  # class-level

    def get_auth_config(self, registry: str, api_client) -> Dict[str, str]:
        if registry not in self._cache:
            header = docker.auth.get_config_header(api_client, registry)
            if header is not None:
                auth_config = json.loads(
                    base64.urlsafe_b64decode(header), encoding="ascii"
                )
            else:
                auth_config = None
            self._cache[registry] = auth_config
        return self._cache[registry]


_auth_cfg_cache = _AuthCfgCache()


class ContainerManager:
    """
    Object managing all containers defined by a given :class:`rcds.Challenge`
    """

    challenge: "Challenge"
    project: "Project"
    config: Dict[str, Dict[str, Any]]
    containers: Dict[str, Container]
    _auth_config: Dict[str, str]

    def __init__(self, challenge: "Challenge"):
        """
        :param rcds.Challenge challenge: The challenge that this ContainerManager
            belongs to
        """

        self.challenge = challenge
        self.project = self.challenge.project
        self.containers = dict()
        self.config = cast(
            Dict[str, Dict[str, Any]], self.challenge.config.get("containers", dict())
        )

        self._auth_config = self._get_auth_config()

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
            container_config["image"] = self.containers[name].get_full_tag()

    def get_docker_image(self, container: Container) -> str:
        image_template = self.project.jinja_env.from_string(
            self.project.config["docker"]["image"]["template"]
        )
        template_context = {
            "challenge": self.challenge.config,
            "container": dict(container.config),
        }
        template_context["container"]["name"] = container.name
        image = image_template.render(template_context)
        # FIXME: better implementation than abusing PosixPath?
        return str(
            PurePosixPath(self.project.config["docker"]["image"]["prefix"]) / image
        )

    def _get_auth_config(self) -> Dict[str, str]:
        registry, _ = docker.auth.resolve_repository_name(
            self.project.config["docker"]["image"]["prefix"]
        )
        return _auth_cfg_cache.get_auth_config(registry, self.project.docker_client.api)
