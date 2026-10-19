"""Facebook OAuth 2.0 authentication handlers."""

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


facebook_config = {
    "access_token_url": "https://graph.facebook.com/v4.0/oauth/access_token",
    "api_base_url": "https://graph.facebook.com/v4.0/",
    "authorize_url": "https://www.facebook.com/v4.0/dialog/oauth",
    "client_id": config.CONFIG_DB.facebook_app_id,
    "client_secret": config.CONFIG_DB.facebook_app_secret,
    "request_token_params": {"scope": "email"},
}

facebook = auth.create_oauth_app(facebook_config, "facebook")


@app.route("/api/auth/callback/facebook/")
def facebook_authorized() -> WerkzeugResponse:
    """Handle Facebook OAuth authorization callback."""
    id_token = facebook.authorize_access_token()
    if id_token is None:
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())

    me = facebook.get("/me?fields=id,name,email")
    user_db = retrieve_user_from_facebook(me.json())
    return auth.signin_user_db(user_db)


@app.route("/signin/facebook/")
def signin_facebook() -> WerkzeugResponse:
    """Initiate Facebook OAuth sign-in flow."""
    return auth.signin_oauth(facebook)


def retrieve_user_from_facebook(response: Mapping[str, Any]) -> model.User:
    """Retrieve existing user by Facebook auth ID or create a new user entity."""
    auth_id = f"facebook_{response['id']}"
    user_db = model.User.get_by("auth_ids", auth_id)
    if user_db:
        return user_db
    name = str(response["name"])
    email = str(response.get("email", ""))
    return auth.create_user_db(
        auth_id=auth_id,
        name=name,
        username=name,
        email=email,
        verified=bool(email),
    )
