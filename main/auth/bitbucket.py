"""Bitbucket OAuth 2.0 authentication handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flask

import auth
import config
import model
import util
from main import app


if TYPE_CHECKING:
    from collections.abc import Mapping

    from werkzeug.wrappers import Response as WerkzeugResponse


bitbucket_config = {
    "access_token_method": "POST",
    "access_token_url": "https://bitbucket.org/site/oauth2/access_token",
    "api_base_url": "https://api.bitbucket.org/2.0/",
    "authorize_url": "https://bitbucket.org/site/oauth2/authorize",
    "client_id": config.CONFIG_DB.bitbucket_key,
    "client_secret": config.CONFIG_DB.bitbucket_secret,
    "client_kwargs": {"scope": "email"},
}

bitbucket = auth.create_oauth_app(bitbucket_config, "bitbucket")


@app.route("/api/auth/callback/bitbucket/")
def bitbucket_authorized() -> WerkzeugResponse:
    """Handle Bitbucket OAuth authorization callback."""
    err = flask.request.args.get("error")
    if err == "access_denied":
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())
    id_token = bitbucket.authorize_access_token()
    if id_token is None:
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())
    me = bitbucket.get("user")
    user_db = retrieve_user_from_bitbucket(me.json())
    return auth.signin_user_db(user_db)


@app.route("/signin/bitbucket/")
def signin_bitbucket() -> WerkzeugResponse:
    """Initiate Bitbucket OAuth sign-in flow."""
    return auth.signin_oauth(bitbucket)


def retrieve_user_from_bitbucket(response: Mapping[str, Any]) -> model.User:
    """Retrieve existing user by Bitbucket username or create a new user entity."""
    username = str(response["username"])
    auth_id = f"bitbucket_{username}"
    user_db = model.User.get_by("auth_ids", auth_id)
    if user_db:
        return user_db
    emails_response = bitbucket.get("user/emails")
    emails = emails_response.json().get("values", [])
    email = "".join([str(e["email"]) for e in emails if e.get("is_primary")][:1])
    return auth.create_user_db(
        auth_id=auth_id,
        name=str(response["display_name"]),
        username=username,
        email=email,
        verified=bool(email),
    )
