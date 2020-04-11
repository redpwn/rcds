from rcds.challenge import docker
from rcds import Project, ChallengeLoader


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

    def test_with_dockerignore(self, datadir) -> None:
        df_root = datadir / "contexts" / "dockerignore"
        assert df_root.is_dir()
        got = {str(p.relative_to(df_root)) for p in docker.get_context_files(df_root)}
        assert got == {"Dockerfile", ".dockerignore", ".file", "file"}


class TestGenerateSum:
    def test_basic(self, datadir):
        df_root = datadir / "contexts" / "basic"
        assert df_root.is_dir()
        # TODO: better way of testing than blackbox hash compare
        assert (
            docker.generate_sum(df_root)
            == "683c5631d14165f0326ef55dfaf5463cc0aa550743398a4d8e31d37c4f5d6981"
        )


class TestContainerManager:
    def test_omnibus(self, datadir):
        proj_root = datadir / "project"
        project = Project(proj_root)
        challenge_loader = ChallengeLoader(project)
        chall = challenge_loader.load(proj_root / "chall")
        container_mgr = docker.ContainerManager(chall)
        assert container_mgr.containers["main"].name == "main"
        assert container_mgr.containers["main"].IS_BUILDABLE
        assert type(container_mgr.containers["main"]) == docker.BuildableContainer
        assert container_mgr.containers["postgres"].name == "postgres"
        assert not container_mgr.containers["postgres"].IS_BUILDABLE
        assert type(container_mgr.containers["postgres"]) == docker.Container
