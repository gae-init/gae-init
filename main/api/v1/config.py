"""Configuration API resources for v1 endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flask_restful

import auth
import config
import model
from api import helpers
from main import api_v1


if TYPE_CHECKING:
    import flask


@api_v1.resource("/admin/config/", endpoint="api.admin.config")
class ConfigAPI(flask_restful.Resource):
    """Resource for inspecting application configuration."""

    @auth.admin_required
    def get(self) -> flask.Response:
        """Return serialized application configuration for administrators."""
        return helpers.make_response(config.CONFIG_DB, model.Config.FIELDS)
