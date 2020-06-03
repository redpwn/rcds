from pathlib import Path
from textwrap import dedent

import pytest  # type: ignore

from rcds import Project, errors
from rcds.challenge import ChallengeLoader


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
    assert chall.config["id"] == "yaml"


def test_load_json_challenge(project: Project, loader: ChallengeLoader) -> None:
    chall = loader.load(project.root / "json")
    assert chall.config["name"] == "Challenge"
    assert chall.config["description"] == "Description"
    assert chall.get_relative_path() == Path("json")
    assert chall.config["id"] == "json"


def test_override_challenge_id(project: Project, loader: ChallengeLoader) -> None:
    chall = loader.load(project.root / "id_override")
    assert chall.config["id"] == "overridden"


def test_load_nonexistent_challenge(project: Project, loader: ChallengeLoader) -> None:
    with pytest.raises(ValueError) as exc:
        loader.load(project.root / "nonexistent")
    assert "No config file found at " in str(exc)


def test_load_bad_dir_name(project: Project, loader: ChallengeLoader) -> None:
    with pytest.raises(errors.SchemaValidationError):
        loader.load(project.root / "bad#dir")


def test_render_description(project: Project, loader: ChallengeLoader) -> None:
    chall = loader.load(project.root / "render-description")
    chall.context["foo"] = "bar"
    assert (
        chall.render_description()
        == dedent(
            """
            # A fancy challenge (render-description)
            **Written by Robert**
            bar
            """
        ).strip()
    )


def test_static_assets(project: Project, loader: ChallengeLoader) -> None:
    chall = loader.load(project.root / "static-assets")
    chall.create_transaction().commit()
    ctx = project.asset_manager.create_context("static-assets")
    assert set(ctx.ls()) == {"file1.txt", "file3.txt"}
    assert (
        ctx.get("file1.txt").read_text()
        == (project.root / "static-assets" / "file1.txt").read_text()
    )
    assert (
        ctx.get("file3.txt").read_text()
        == (project.root / "static-assets" / "file2.txt").read_text()
    )
