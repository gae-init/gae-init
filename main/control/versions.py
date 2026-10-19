"""Dependency and package version inspection utility."""

import importlib
import importlib.metadata

from opentelemetry import trace


MODULES = [
    "aniso8601",
    "Authlib|authlib",
    "blinker",
    "certifi",
    "click",
    "cryptography",
    "Flask|flask",
    "Flask-Login|flask_login",
    "Flask-RESTful|flask_restful.__version__",
    "Flask-WTF|flask_wtf",
    "itsdangerous",
    "ipaddress",
    "Jinja2|jinja2",
    "marshmallow",
    "requests",
    "Unidecode|unidecode",
    "webargs",
    "Werkzeug|werkzeug",
    "WTForms|wtforms",
]

tracer = trace.get_tracer(__name__)


def get_module_version(spec: str) -> tuple[str, str]:
    """Retrieve version information for a given module specification."""
    names = spec.split("|", 1)
    try:
        module = importlib.import_module(names[-1])
    except ImportError:
        return (names[0], "ERROR: Cannot import")
    version = getattr(module, "__version__", "n/a")
    return (names[0], version)


def get_versions(*, working_set: bool = True) -> list[tuple[str, str]]:
    """Collect versions of tracked modules and installed distributions."""
    with tracer.start_as_current_span("collect_versions"):
        versions = [get_module_version(name) for name in MODULES]
        if working_set:
            versions.extend(
                (f"{dist.metadata['Name']} *", dist.version)
                for dist in importlib.metadata.distributions()
            )
        versions.sort()
    return versions
