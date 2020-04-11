from rcds.challenge import ChallengeLoader
from rcds import Project
from pathlib import Path
import pytest  # type: ignore


@pytest.fixture
def project(datadir) -> Project:
    return Project(datadir)


@pytest.fixture
def loader(project) -> ChallengeLoader:
    return ChallengeLoader(project)


def test_load_yaml_challenge(project: Project, loader: ChallengeLoader) -> None:
    chall = loader.load(project.root / "yaml")
    assert chall.config["name"] == "Challenge"
    assert chall.config["description"] == "Description"
    assert chall.get_relative_path() == Path("yaml")


def test_load_json_challenge(project: Project, loader: ChallengeLoader) -> None:
    chall = loader.load(project.root / "json")
    assert chall.config["name"] == "Challenge"
    assert chall.config["description"] == "Description"
    assert chall.get_relative_path() == Path("json")


def test_load_nonexistent_challenge(project: Project, loader: ChallengeLoader) -> None:
    with pytest.raises(ValueError) as exc:
        loader.load(project.root / "nonexistent")
    assert "No config file found at " in str(exc)
