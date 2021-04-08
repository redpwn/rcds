from pathlib import Path
from typing import cast

import pytest  # type: ignore

from rcds import ChallengeLoader, Project
from rcds.challenge import docker


class TestGetContextFiles:
    def test_basic(self, datadir) -> None:
        df_root = datadir / "contexts" / "basic"
        assert df_root.is_dir()
        got = {str(p.relative_to(df_root)) for p in docker.get_context_files(df_root)}
        assert got == {
            "Dockerfile",
            "file",
            "a/file",
            "a/b/file",
            ".file",
            "a/.file",
            "a/b/.file",
        }

    def test_with_dockerignore(self, datadir: Path) -> None:
        df_root = datadir / "contexts" / "dockerignore"
        assert df_root.is_dir()
        got = {str(p.relative_to(df_root)) for p in docker.get_context_files(df_root)}
        assert got == {"Dockerfile", ".file", "file"}

    def test_complex_dockerignore(self, datadir: Path) -> None:
        df_root = datadir / "contexts" / "complex_dockerignore"
        assert df_root.is_dir()
        got = {str(p.relative_to(df_root)) for p in docker.get_context_files(df_root)}
        assert got == {"a", "b", "c/file", "d/file"}


class TestGenerateSum:
    def test_basic(self, datadir) -> None:
        df_root = datadir / "contexts" / "basic"
        assert df_root.is_dir()
        # TODO: better way of testing than blackbox hash compare
        assert (
            docker.generate_sum(df_root)
            == "683c5631d14165f0326ef55dfaf5463cc0aa550743398a4d8e31d37c4f5d6981"
        )


class TestContainerManager:
    @pytest.fixture()
    def project(self, datadir: Path) -> Project:
        return Project(datadir / "project")

    def test_omnibus(self, project: Project) -> None:
        challenge_loader = ChallengeLoader(project)
        chall = challenge_loader.load(project.root / "chall")
        container_mgr = docker.ContainerManager(chall)

        simple_container = container_mgr.containers["simple"]
        assert simple_container.name == "simple"
        assert simple_container.IS_BUILDABLE
        assert type(simple_container) == docker.BuildableContainer
        simple_container = cast(docker.BuildableContainer, simple_container)
        assert simple_container.get_full_tag().startswith("registry.com/ns/")
        assert "simple" in simple_container.get_full_tag()
        assert chall.config["containers"]["simple"]["image"].startswith(
            "registry.com/ns/"
        )
        assert "simple" in chall.config["containers"]["simple"]["image"]
        assert simple_container.dockerfile == "Dockerfile"
        assert simple_container.buildargs == dict()

        complex_container = container_mgr.containers["complex"]
        assert complex_container.name == "complex"
        assert complex_container.IS_BUILDABLE
        assert type(complex_container) == docker.BuildableContainer
        complex_container = cast(docker.BuildableContainer, complex_container)
        assert complex_container.get_full_tag().startswith("registry.com/ns/")
        assert "complex" in complex_container.get_full_tag()
        assert chall.config["containers"]["complex"]["image"].startswith(
            "registry.com/ns/"
        )
        assert "complex" in chall.config["containers"]["complex"]["image"]
        assert complex_container.dockerfile == "Dockerfile.alternate"
        assert complex_container.buildargs["foo"] == "bar"

        pg_container = container_mgr.containers["postgres"]
        assert pg_container.name == "postgres"
        assert not pg_container.IS_BUILDABLE
        assert type(pg_container) == docker.Container
        assert pg_container.get_full_tag() == "postgres"

    def test_multiple_chall_independence(self, project) -> None:
        challenge_loader = ChallengeLoader(project)
        chall1 = challenge_loader.load(project.root / "chall")
        chall2 = challenge_loader.load(project.root / "chall2")
        chall1_mgr = docker.ContainerManager(chall1)
        chall2_mgr = docker.ContainerManager(chall2)

        assert "chall2ctr" not in chall1_mgr.containers
        assert "postgres" not in chall2_mgr.containers
