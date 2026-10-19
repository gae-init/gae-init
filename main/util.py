"""Application utility functions and request helpers."""

from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from typing import TYPE_CHECKING, Any, TypeGuard
from urllib.parse import urlencode, urlparse
from uuid import uuid4

import flask
from google.cloud import ndb
from marshmallow import EXCLUDE
from webargs import fields as wf
from webargs.flaskparser import parser

import config


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


###############################################################################
# Environment Variables
###############################################################################
def get_env_str(key: str, default: str | None) -> str | None:
    """Fetch an environment variable and safely cast to str, falling back to default."""
    val = os.environ.get(key)
    if val is not None:
        return val
    return default


def get_env_int(key: str, default: int) -> int:
    """Fetch an environment variable and safely cast to int, falling back to default."""
    val = os.environ.get(key)
    if val is not None and val.isdigit():
        return int(val)
    return default


###############################################################################
# Request Parameters
###############################################################################
def param(name: str, cast: object | None = None) -> Any:  # noqa: ANN401
    """Parse a single parameter from the request query or JSON payload."""

    def switch(case: object) -> wf.Field | None:
        return {
            int: wf.Int(load_default=None),
            float: wf.Float(load_default=None),
            bool: wf.Bool(load_default=None),
            list: wf.DelimitedList(wf.Str(), delimiter=",", load_default=[]),
        }.get(case)  # type: ignore[call-overload]

    if cast is None or cast is ndb.Key:
        cast_field: wf.Field = wf.Str(load_default=None)
    else:
        switched = switch(cast)
        if switched is not None:
            cast_field = switched
        elif isinstance(cast, wf.Field):
            cast_field = cast
        else:
            cast_field = wf.Str(load_default=None)

    if flask.request.method in ["GET", "DELETE"] or name in flask.request.args:
        location = "query"
    elif flask.request.is_json:
        location = "json"
    else:
        location = "form"

    args = parser.parse(
        {name: cast_field},
        location=location,
        unknown=EXCLUDE,
    )
    value = args[name]
    return ndb.Key(urlsafe=value) if cast is ndb.Key and value else value


def is_trusted_url(next_url: str | None) -> str:
    """Validate whether a redirect URL is trusted, falling back to welcome URL."""
    if not next_url:
        return ""
    next_url_host = urlparse(next_url).hostname
    if config.TRUSTED_HOSTS and next_url_host not in config.TRUSTED_HOSTS:
        return flask.url_for("welcome")
    if not next_url.startswith(flask.request.host_url):
        return flask.url_for("welcome")
    return next_url


def get_next_url(next_url: str = "") -> str:
    """Determine the next URL for redirection from parameters or referrer."""
    if (
        flask.request.method in ["GET", "DELETE"]
        or "next" in flask.request.args
        or "next_url" in flask.request.args
    ):
        location = "query"
    elif flask.request.is_json:
        location = "json"
    else:
        location = "form"

    args = parser.parse(
        {"next": wf.Str(load_default=None), "next_url": wf.Str(load_default=None)},
        location=location,
        unknown=EXCLUDE,
    )
    resolved_url = next_url or args["next"] or args["next_url"]
    if resolved_url:
        do_not_redirect_urls = [
            flask.url_for(u)
            for u in [
                "signin",
                "signup",
                "user_forgot",
                "user_reset",
            ]
        ]
        if any(url in resolved_url for url in do_not_redirect_urls):
            return flask.url_for("welcome")
        return is_trusted_url(resolved_url)
    return is_trusted_url(flask.request.referrer)


###############################################################################
# Model manipulations
###############################################################################
def get_dbs(  # noqa: C901, PLR0913, PLR0917
    query: ndb.Query,
    order: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    prev_cursor: bool = False,  # noqa: FBT001, FBT002
    keys_only: bool | None = None,  # noqa: FBT001
    **filters: object,
) -> tuple[list[Any], dict[str, str | None]]:
    """Query datastore entities with ordering, filtering, and cursor pagination."""
    model_class = ndb.Model._kind_map[query.kind]  # noqa: SLF001
    if order:
        for o in order.split(","):
            if o.startswith("-"):
                query = query.order(-model_class._properties[o[1:]])  # noqa: SLF001
            else:
                query = query.order(model_class._properties[o])  # noqa: SLF001

    for prop, value in filters.items():
        if value is None:
            continue
        for val in value if isinstance(value, list) else [value]:
            query = query.filter(model_class._properties[prop] == val)  # noqa: SLF001

    limit = limit or config.DEFAULT_DB_LIMIT
    if limit == -1:
        return list(query.fetch(keys_only=keys_only)), {"next": None, "prev": None}

    cursors = cursor.split(",") if cursor else []
    current_cursor = cursors[-1] if cursors else None
    cursor_obj = ndb.Cursor.from_websafe_string(current_cursor) if current_cursor else None

    model_dbs, next_cursor_obj, more = query.fetch_page(
        limit,
        start_cursor=cursor_obj,
        keys_only=keys_only,
    )
    if len(model_dbs) < limit:
        more = False

    next_cursor_str = (
        next_cursor_obj.to_websafe_string().decode("utf-8") if more and next_cursor_obj else None
    )
    next_cursor_enc = ",".join([*cursors, next_cursor_str]) if next_cursor_str else None

    if not prev_cursor:
        return list(model_dbs), {"next": next_cursor_enc, "prev": None}

    if cursors:
        prev_cursors = cursors[:-1]
        prev_cursor_enc = ",".join(prev_cursors)
    else:
        prev_cursor_enc = None

    return list(model_dbs), {"next": next_cursor_enc, "prev": prev_cursor_enc}


def get_keys(
    query: ndb.Query,
    order: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    prev_cursor: bool = False,  # noqa: FBT001, FBT002
    **filters: object,
) -> tuple[list[Any], dict[str, str | None]]:
    """Fetch only keys for entities matching the query."""
    return get_dbs(
        query,
        order=order,
        limit=limit,
        cursor=cursor,
        prev_cursor=prev_cursor,
        keys_only=True,
        **filters,
    )


###############################################################################
# JSON Response Helpers
###############################################################################
def jsonpify(*args: object, **kwargs: object) -> flask.Response:
    """Return JSON or JSONP response if callback parameter is present."""
    params = parser.parse({"callback": wf.Str(load_default=None)}, location="query")
    if params["callback"]:
        res = flask.jsonify(*args, **kwargs)
        content = f"{params['callback']}({res.get_data(as_text=True)})"
        response = flask.make_response(content)
        response.mimetype = "application/javascript"
        return response
    return flask.jsonify(*args, **kwargs)


###############################################################################
# Helpers
###############################################################################
def is_iterable(value: object) -> TypeGuard[Sequence[object]]:
    """Check if value is a tuple or list."""
    return isinstance(value, (tuple, list))


def check_form_fields(*fields: object) -> bool:
    """Check if all provided WTForms fields contain non-empty data."""
    fields_data = []
    for field in fields:
        if is_iterable(field):
            fields_data.extend([getattr(f, "data", None) for f in field])
        else:
            fields_data.append(getattr(field, "data", None))
    return all(fields_data)


def generate_next_url(
    next_cursor: dict[str, str | None] | str | None,
    base_url: str | None = None,
    cursor_name: str = "cursor",
) -> str | None:
    """Generate next page URL preserving existing query parameters."""
    if isinstance(next_cursor, dict):
        next_cursor = next_cursor.get("next")
    if next_cursor is None:
        return None
    base_url = base_url or flask.request.base_url
    args = flask.request.args.to_dict()
    if next_cursor == "":
        args.pop(cursor_name, None)
    else:
        args[cursor_name] = next_cursor
    query_str = urlencode(args)
    return f"{base_url}?{query_str}" if query_str else base_url


def uuid() -> str:
    """Generate a random UUID hex string."""
    return uuid4().hex


_slugify_strip_re = re.compile(r"[^\w\s-]")
_slugify_hyphenate_re = re.compile(r"[-\s]+")


def slugify(text: object) -> str:
    """Generate a URL-friendly slug from text."""
    if not isinstance(text, str):
        text = str(text)
    # Using 'ascii' with 'ignore' explicitly strips out non-ascii characters
    # (e.g. accents) after NFKD normalization. Do not change to 'utf-8'.
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = str(_slugify_strip_re.sub("", text).strip().lower())
    return _slugify_hyphenate_re.sub("-", text)


_username_re = re.compile(r"^[a-z0-9]+(?:[\.][a-z0-9]+)*$")


def is_valid_username(username: str) -> bool:
    """Validate username format (alphanumeric and dot-separated)."""
    return bool(_username_re.match(username))


def create_name_from_email(email: str) -> str:
    """Derive a human-readable display name from an email local part."""
    return re.sub(r"_+|-+|\.+|\++", " ", email.split("@", maxsplit=1)[0]).title()


def password_hash(user_db: object, password: str | None) -> str:
    """Compute sha256 password hash using user key, created timestamp, and salt."""
    m = hashlib.sha256()
    key = getattr(user_db, "key", None)
    urlsafe = key.urlsafe() if key else b""
    if isinstance(urlsafe, str):
        urlsafe = urlsafe.encode("utf-8")
    m.update(urlsafe)
    created = getattr(user_db, "created", None)
    if created is not None:
        m.update(created.isoformat().encode("utf-8"))
    m.update(m.hexdigest().encode("utf-8"))
    if password:
        m.update(password.encode("utf-8"))
    salt = config.CONFIG_DB.salt
    m.update(salt.encode("utf-8") if isinstance(salt, str) else salt)
    return m.hexdigest()


def update_query_argument(
    name: str,
    value: str | None = None,
    ignore: str | Sequence[str] = "cursor",
    is_list: bool = False,  # noqa: FBT001, FBT002
) -> str:
    """Update or remove a query argument in the current request URL."""
    ignore_list = ignore.split(",") if isinstance(ignore, str) else ignore or []
    arguments = {
        key: val
        for key, val in flask.request.args.items()
        if key not in ignore_list and ((is_list and value is not None) or key != name)
    }
    if value is not None:
        if is_list:
            values = []
            if name in arguments:
                values = arguments[name].split(",")
                del arguments[name]
            if value in values:
                values.remove(value)
            else:
                values.append(value)
            if values:
                arguments[name] = ",".join(values)
        else:
            arguments[name] = value
    query = "&".join(f"{k}={v}" for k, v in sorted(arguments.items()))
    query_part = f"?{query}" if query else ""
    return f"{flask.request.path}{query_part}"


def parse_tags(tags: str | Iterable[str], separator: str | None = None) -> list[str]:
    """Parse comma/delimiter-separated tags into a unique sorted list."""
    if not is_iterable(tags):
        tag_items = str(tags).strip().split(separator or config.TAG_SEPARATOR)
    else:
        tag_items = [str(t) for t in tags]
    return list(filter(None, sorted(set(tag_items))))


###############################################################################
# Lambdas
###############################################################################
def strip_filter(x: str | None) -> str:
    """Strip leading and trailing whitespace if value is non-empty."""
    return x.strip() if x else ""


def email_filter(x: str | None) -> str:
    """Lower-case and strip whitespace from an email string if non-empty."""
    return x.lower().strip() if x else ""


def sort_filter(x: Iterable[Any] | None) -> list[Any]:
    """Sort an iterable if non-empty, returning a list."""
    return sorted(x) if x else []
