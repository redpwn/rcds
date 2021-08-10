from textwrap import dedent
from typing import Any, Dict, List, Optional

import yaml
from jinja2 import Environment, PackageLoader, filters

jinja_env = Environment(
    loader=PackageLoader("rcds.backends.k8s", "templates"),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def jinja_filter_indent(data: str, *args, **kwargs) -> str:
    return filters.do_indent(dedent(data), *args, **kwargs)


def jinja_filter_yaml(data: Dict[str, Any], indent: Optional[int] = None) -> str:
    output = yaml.dump(data).strip()
    if indent is not None:
        output = jinja_filter_indent(output, indent)
    return output


def jinja_filter_pick(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if k in keys}


def jinja_filter_omit(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if k not in keys}


jinja_env.filters["indent"] = jinja_filter_indent
jinja_env.filters["yaml"] = jinja_filter_yaml
jinja_env.filters["quote"] = lambda s: repr(str(s))
jinja_env.filters["pick"] = jinja_filter_pick
jinja_env.filters["omit"] = jinja_filter_omit
