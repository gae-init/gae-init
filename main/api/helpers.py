"""API helper classes and utility functions."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, NoReturn

import flask
import flask_restful
from werkzeug import exceptions

import util


if TYPE_CHECKING:
    from collections.abc import Mapping


logger = logging.getLogger(__name__)


class Api(flask_restful.Api):
    """Custom API router for JSON responses and standard error handling."""

    def unauthorized(self, response: flask.Response) -> None:  # noqa: ARG002
        """Abort with HTTP 401 Unauthorized."""
        flask.abort(401)

    def handle_error(self, e: Exception) -> tuple[flask.Response, int]:
        """Delegate API error formatting."""
        return handle_error(e)


def handle_error(e: Exception) -> tuple[flask.Response, int]:
    """Format an exception into a consistent JSON response with status code."""
    logger.error("API exception caught: %s", e)
    code = getattr(e, "code", 500)
    name = getattr(e, "name", "Internal Server Error")
    description = getattr(e, "description", "Internal Server Error")
    return (
        util.jsonpify(
            {
                "status": "error",
                "error_code": code,
                "error_name": util.slugify(name),
                "error_message": name,
                "error_class": e.__class__.__name__,
                "description": description,
            }
        ),
        code,
    )


def make_response(
    data: object,
    marshal_table: Mapping[str, object],
    cursors: dict[str, str | None] | str | None = None,
) -> flask.Response:
    """Marshal response data and cursors into a standard JSON success payload."""
    now_iso = datetime.now(UTC).isoformat()
    if isinstance(data, (list, tuple)):
        response: dict[str, object] = {
            "status": "success",
            "count": len(data),
            "now": now_iso,
            "result": [flask_restful.marshal(d, marshal_table) for d in data],
        }
        if cursors:
            if isinstance(cursors, dict):
                if cursors.get("next"):
                    response["next_cursor"] = cursors["next"]
                    response["next_url"] = util.generate_next_url(cursors["next"])
                if cursors.get("prev"):
                    response["prev_cursor"] = cursors["prev"]
                    response["prev_url"] = util.generate_next_url(cursors["prev"])
            else:
                response["next_cursor"] = cursors
                response["next_url"] = util.generate_next_url(cursors)
        return util.jsonpify(response)
    return util.jsonpify(
        {
            "status": "success",
            "now": now_iso,
            "result": flask_restful.marshal(data, marshal_table),
        }
    )


def make_not_found_exception(description: str) -> NoReturn:
    """Raise a NotFound exception with the specified description."""
    exception = exceptions.NotFound()
    exception.description = description
    raise exception
