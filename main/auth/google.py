"""Google OAuth 2.0 authentication handlers."""

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


google_config = {
    "access_token_method": "POST",
    "access_token_url": "https://accounts.google.com/o/oauth2/token",
    "api_base_url": "https://www.googleapis.com/oauth2/v1/",
    "authorize_url": "https://accounts.google.com/o/oauth2/auth",
    "client_id": config.CONFIG_DB.google_client_id,
    "client_secret": config.CONFIG_DB.google_client_secret,
    "client_kwargs": {"scope": "email profile"},
}

google = auth.create_oauth_app(google_config, "google")


@app.route("/api/auth/callback/google/")
def google_authorized() -> WerkzeugResponse:
    """Handle Google OAuth authorization callback."""
    id_token = google.authorize_access_token()
    if id_token is None:
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())

    me = google.get("userinfo")
    user_db = retrieve_user_from_google(me.json())
    return auth.signin_user_db(user_db)


@app.route("/signin/google/")
def signin_google() -> WerkzeugResponse:
    """Initiate Google OAuth sign-in flow."""
    return auth.signin_oauth(google)


def retrieve_user_from_google(response: Mapping[str, Any]) -> model.User:
    """Retrieve existing user by Google auth ID or create a new user entity."""
    user_id = response["id"]
    auth_id = f"google_{user_id}"
    user_db = model.User.get_by("auth_ids", auth_id)
    if user_db:
        return user_db

    name = response.get("name", "")
    if not name:
        given_name = response.get("given_name", "")
        family_name = response.get("family_name", "")
        name = f"{given_name} {family_name}".strip()
    if not name:
        name = f"google_user_{user_id}"
    email = str(response.get("email", ""))
    return auth.create_user_db(
        auth_id=auth_id,
        name=name,
        username=email or name,
        email=email,
        verified=bool(email),
    )
