from rcds.challenge import config
import pytest  # type: ignore


@pytest.fixture
def test_datadir(request, datadir):
    fn_name = request.function.__name__
    assert fn_name[:5] == "test_"
    return datadir / fn_name[5:]


def test_valid(test_datadir) -> None:
    cfg, errors = config.check_config(test_datadir / "challenge.yml")
    assert errors is None


def test_expose_no_containers(test_datadir) -> None:
    cfg, errors = config.check_config(test_datadir / "challenge.yml")
    assert errors is not None
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert "Cannot expose ports without containers defined" in error_messages


def test_nonexistent_target_container(test_datadir) -> None:
    cfg, errors = config.check_config(test_datadir / "challenge.yml")
    assert errors is not None
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert (
        '`expose` references container "main" but it is not defined in `containers`'
        in error_messages
    )


def test_nonexistent_target_port(test_datadir):
    cfg, errors = config.check_config(test_datadir / "challenge.yml")
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert (
        '`expose` references port 1 on container "main" which is not defined'
        in error_messages
    )


def test_nonexistent_provide_file(test_datadir):
    cfg, errors = config.check_config(test_datadir / "challenge.yml")
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert (
        '`provide` references file "nonexistent" which does not exist' in error_messages
    )


def test_nonexistent_flag_file(test_datadir):
    cfg, errors = config.check_config(test_datadir / "challenge.yml")
    errors = list(errors)
    error_messages = [str(e) for e in errors]
    assert len(errors) != 0
    assert (
        '`flag.file` references file "nonexistent" which does not exist'
        in error_messages
    )
