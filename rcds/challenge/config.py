from itertools import tee
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional, Tuple, Union

import jsonschema.exceptions  # type: ignore
from jsonschema import Draft7Validator  # type: ignore

from ..util import load_any

if TYPE_CHECKING:  # pragma: no cover
    from rcds import Project


config_schema_validator = Draft7Validator(
    schema=load_any(Path(__file__).parent / "challenge.schema.yaml")
)


class ConfigLoader:
    """
    Object that manages loading challenge config files
    """

    project: "Project"

    def __init__(self, project: "Project"):
        """
        :param rcds.Project project: project context to use
        """
        self.project = project

    def check_config(
        self, config_file: Path,
    ) -> Tuple[
        dict,
        Optional[Iterable[Union[jsonschema.exceptions.ValidationError, Exception]]],
    ]:
        """
        Load and validate a config file, returning any errors encountered.

        If the config file is valid, the tuple returned contains the loaded config as
        the first element, and the second element is None. Otherwise, the second
        element is an iterable of errors that occurred during validation

        :param pathlib.Path config_file: The challenge config to load
        """
        root = config_file.parent
        config = load_any(config_file)

        def check() -> Iterable[
            Union[jsonschema.exceptions.ValidationError, Exception]
        ]:
            schema_errors = config_schema_validator.iter_errors(config)
            # Make a duplicate to check whethere there are errors returned
            schema_errors, schema_errors_dup = tee(schema_errors)
            # This is the same test as used in Validator.is_valid
            if next(schema_errors_dup, None) is not None:
                yield from schema_errors
            else:
                if "expose" in config:
                    if "containers" not in config:
                        # FIXME: Use better error types
                        yield ValueError(
                            "Cannot expose ports without containers defined"
                        )
                    else:
                        for key, expose_objs in config["expose"].items():
                            if key not in config["containers"]:
                                # FIXME: Use better error types
                                yield ValueError(
                                    f'`expose` references container "{key}" but '
                                    f"it is not defined in `containers`"
                                )
                            else:
                                for expose_obj in expose_objs:
                                    if (
                                        expose_obj["target"]
                                        not in config["containers"][key]["ports"]
                                    ):
                                        # FIXME: Use better error types
                                        yield ValueError(
                                            f"`expose` references port "
                                            f'{expose_obj["target"]} on container '
                                            f'"{key}" which is not defined'
                                        )
                if "provide" in config:
                    for f in config["provide"]:
                        f = Path(f)
                        if not (root / f).is_file():
                            # FIXME: Use better error types
                            yield FileNotFoundError(
                                f'`provide` references file "{str(f)}" which does not '
                                f"exist"
                            )
                if "flag" in config and isinstance(config["flag"], dict):
                    if "file" in config["flag"]:
                        f = Path(config["flag"]["file"])
                        if not (root / f).is_file():
                            # FIXME: Use better error types
                            yield FileNotFoundError(
                                f'`flag.file` references file "{str(f)}" which does '
                                f"not exist"
                            )

        errors = check()
        errors, errors_dup = tee(errors)
        has_errors = next(errors_dup, None) is not None
        return (config, errors if has_errors else None)

    def load_config(self, config_file: Path) -> dict:
        """
        Loads a config file, or throw an exception if it is not valid

        This method wraps :meth:`check_config`, and throws the first error returned
        if there are any errors

        :returns: The loaded config
        """
        config, errors = self.check_config(config_file)
        if errors is not None:
            raise next(iter(errors))
        return config
