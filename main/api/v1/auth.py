"""Authentication API resources for v1 endpoints."""

from __future__ import annotations

import flask
import flask_restful
from marshmallow import EXCLUDE
from webargs import fields as wf
from webargs.flaskparser import parser

import auth
import model
import util
from api import helpers
from main import api_v1


@api_v1.resource("/auth/signin/", endpoint="api.auth.signin")
class AuthAPI(flask_restful.Resource):
    """Resource for authenticating users via API."""

    def post(self) -> flask.Response:
        """Authenticate user credentials and return serialized user data."""
        args = parser.parse(
            {
                "username": wf.Str(load_default=None),
                "email": wf.Str(load_default=None),
                "password": wf.Str(load_default=None),
            },
            location="json_or_form",
            unknown=EXCLUDE,
        )
        handler = args["username"] or args["email"]
        password = args["password"]
        if not handler or not password:
            flask.abort(400)

        user_db = model.User.get_by("email" if "@" in handler else "username", handler.lower())

        if user_db and user_db.password_hash == util.password_hash(user_db, password):
            auth.signin_user_db(user_db)
            return helpers.make_response(user_db, model.User.FIELDS)
        return flask.abort(401)
