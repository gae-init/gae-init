"""Microsoft OAuth 2.0 authentication handlers."""

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


microsoft_config = {
    "access_token_method": "POST",
    "access_token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
    "api_base_url": "https://graph.microsoft.com/v1.0/",
    "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    "client_id": config.CONFIG_DB.microsoft_client_id,
    "client_secret": config.CONFIG_DB.microsoft_client_secret,
    "client_kwargs": {"scope": "user.read"},
}

microsoft = auth.create_oauth_app(microsoft_config, "microsoft")


@app.route("/api/auth/callback/microsoft/")
def microsoft_authorized() -> WerkzeugResponse:
    """Handle Microsoft OAuth authorization callback."""
    err = flask.request.args.get("error")
    if err == "access_denied":
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())
    id_token = microsoft.authorize_access_token()
    if id_token is None:
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())
    me = microsoft.get("me")
    user_db = retrieve_user_from_microsoft(me.json())
    return auth.signin_user_db(user_db)


@app.route("/signin/microsoft/")
def signin_microsoft() -> WerkzeugResponse:
    """Initiate Microsoft OAuth sign-in flow."""
    return auth.signin_oauth(microsoft)


def retrieve_user_from_microsoft(response: Mapping[str, Any]) -> model.User:
    """Retrieve existing user by Microsoft auth ID or create a new user entity."""
    auth_id = f"microsoft_{response['id']}"
    user_db = model.User.get_by("auth_ids", auth_id)
    if user_db:
        return user_db
    email = str(response["userPrincipalName"])
    name = str(response.get("displayName", ""))
    return auth.create_user_db(
        auth_id=auth_id,
        name=name,
        username=name or email,
        email=email,
        verified=bool(email),
    )
