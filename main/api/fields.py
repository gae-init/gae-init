"""Custom serialization fields for Flask-RESTful API resources."""

from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING

from flask_restful import fields
from flask_restful.fields import (
    Boolean,
    Float,
    FormattedString,
    List,
    Nested,
    Raw,
    String,
    Url,
)


if TYPE_CHECKING:
    import datetime as dt

    from google.cloud import ndb


_JS_MAX_SAFE_INTEGER = 9007199254740992


class BlobKey(fields.Raw):
    """Format BlobKey values as URL-quoted strings."""

    def format(self, value: object) -> str:
        """Format blob key."""
        return urllib.parse.quote(str(value))


class Blob(fields.Raw):
    """Format raw Blob values as string representations."""

    def format(self, value: object) -> str:
        """Format blob value."""
        return repr(value)


class DateTime(fields.DateTime):
    """Format datetime objects to ISO format strings."""

    def format(self, value: dt.date | dt.datetime) -> str:
        """Format datetime to ISO 8601 string."""
        return value.isoformat()


class GeoPt(fields.Raw):
    """Format App Engine GeoPt objects as 'lat,lon' strings."""

    def format(self, value: object) -> str:
        """Format latitude and longitude."""
        lat = getattr(value, "lat", "")
        lon = getattr(value, "lon", "")
        return f"{lat},{lon}"


class Id(fields.Raw):
    """Extract and output an entity ID from an NDB model key."""

    def output(self, key: str, obj: object) -> object:
        """Output entity ID from entity key if present."""
        try:
            entity_key = getattr(obj, "key", None)
            value = entity_key.id() if entity_key is not None else None
            return super().output(key, {"id": value})
        except AttributeError:
            return None


class Integer(fields.Integer):
    """Format integers, stringifying values beyond JavaScript safe integer bounds."""

    def format(self, value: int) -> int | str:
        """Format integer value safely for JavaScript consumption."""
        if value > _JS_MAX_SAFE_INTEGER or value < -_JS_MAX_SAFE_INTEGER:
            return str(value)
        return value


class Key(fields.Raw):
    """Format NDB Key instances as URL-safe strings."""

    def format(self, value: ndb.Key | object) -> str:
        """Format NDB key to URL-safe string."""
        urlsafe = getattr(value, "urlsafe", lambda: b"")()
        if isinstance(urlsafe, bytes):
            return urlsafe.decode("utf-8")
        return str(urlsafe)


__all__ = [
    "Blob",
    "BlobKey",
    "Boolean",
    "DateTime",
    "Float",
    "FormattedString",
    "GeoPt",
    "Id",
    "Integer",
    "Key",
    "List",
    "Nested",
    "Raw",
    "String",
    "Url",
]
