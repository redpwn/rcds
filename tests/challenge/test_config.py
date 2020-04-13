import pytest  # type: ignore

import rcds
from rcds import Project
from rcds.challenge import config


@pytest.fixture
def test_datadir(request, datadir):
    fn_name = request.function.__name__
    assert fn_name[:5] == "test_"
    return datadir / fn_name[5:]


@pytest.fixture
def configloader(datadir):
    project = Project(datadir)
    return config.ConfigLoader(project)


def test_valid(configloader, test_datadir) -> None:
    cfg, errors = configloader.check_config(test_datadir / "challenge.yml")
    assert errors is None


def test_schema_fail(configloader, test_datadir) -> None:
    cfg, errors = configloader.check_config(test_datadir / "challenge.yml")
    assert errors is not None
    assert cfg is None
    errors = list(errors)
    assert (
        sum([1 for e in errors if isinstance(e, rcds.errors.SchemaValidationError)]) > 0
    )


def test_expose_no_containers(configloader, test_datadir) -> None:
    cfg, errors = configloader.check_config(test_datadir / "challenge.yml")
    assert errors is not None
    assert cfg is None
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert "Cannot expose ports without containers defined" in error_messages
    assert sum([1 for e in errors if isinstance(e, config.TargetNotFoundError)]) == 1


def test_nonexistent_target_container(configloader, test_datadir) -> None:
    cfg, errors = configloader.check_config(test_datadir / "challenge.yml")
    assert errors is not None
    assert cfg is None
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert (
        '`expose` references container "main" but it is not defined in `containers`'
        in error_messages
    )
    assert sum([1 for e in errors if isinstance(e, config.TargetNotFoundError)]) == 1


def test_nonexistent_target_port(configloader, test_datadir) -> None:
    cfg, errors = configloader.check_config(test_datadir / "challenge.yml")
    assert errors is not None
    assert cfg is None
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert (
        '`expose` references port 1 on container "main" which is not defined'
        in error_messages
    )
    assert sum([1 for e in errors if isinstance(e, config.TargetNotFoundError)]) == 1


def test_nonexistent_provide_file(configloader, test_datadir) -> None:
    cfg, errors = configloader.check_config(test_datadir / "challenge.yml")
    assert errors is not None
    assert cfg is None
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert (
        '`provide` references file "nonexistent" which does not exist' in error_messages
    )
    assert (
        sum([1 for e in errors if isinstance(e, config.TargetFileNotFoundError)]) == 1
    )


def test_nonexistent_flag_file(configloader, test_datadir) -> None:
    cfg, errors = configloader.check_config(test_datadir / "challenge.yml")
    assert errors is not None
    assert cfg is None
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert (
        '`flag.file` references file "nonexistent" which does not exist'
        in error_messages
    )
    assert (
        sum([1 for e in errors if isinstance(e, config.TargetFileNotFoundError)]) == 1
    )


def test_load_valid(configloader: config.ConfigLoader, datadir) -> None:
    cfg = configloader.load_config(datadir / "valid/challenge.yml")
    assert cfg is not None


def test_load_invalid(configloader: config.ConfigLoader, datadir) -> None:
    with pytest.raises(Exception):
        configloader.load_config(datadir / "nonexistent_flag_file/challenge.yml")
