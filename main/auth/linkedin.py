"""LinkedIn OAuth 2.0 authentication handlers."""

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


linkedin_config = {
    "access_token_method": "POST",
    "access_token_url": "https://www.linkedin.com/uas/oauth2/accessToken",
    "api_base_url": "https://api.linkedin.com/v2/",
    "authorize_url": "https://www.linkedin.com/uas/oauth2/authorization",
    "client_id": config.CONFIG_DB.linkedin_api_key,
    "client_secret": config.CONFIG_DB.linkedin_secret_key,
    "client_kwargs": {
        "scope": "r_liteprofile r_emailaddress",
        "state": util.uuid(),
        "token_endpoint_auth_method": "client_secret_post",
    },
}


linkedin = auth.create_oauth_app(linkedin_config, "linkedin")


@app.route("/api/auth/callback/linkedin/")
def linkedin_authorized() -> WerkzeugResponse:
    """Handle LinkedIn OAuth authorization callback."""
    err = flask.request.args.get("error")
    if err in ["user_cancelled_login", "user_cancelled_authorize"]:
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())
    id_token = linkedin.authorize_access_token()
    if id_token is None:
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())
    me = linkedin.get("me?projection=(id,firstName,lastName)")
    user_db = retrieve_user_from_linkedin(me.json())
    return auth.signin_user_db(user_db)


@app.route("/signin/linkedin/")
def signin_linkedin() -> WerkzeugResponse:
    """Initiate LinkedIn OAuth sign-in flow."""
    return auth.signin_oauth(linkedin)


def dict_gets(
    dct: Any,  # noqa: ANN401
    k: str,
    default: object = None,
    sep: str = "|",
) -> Any:  # noqa: ANN401
    """Look up a nested value in a dict by walking a separated path."""
    keys = k.split(sep)
    data = dct
    try:
        for key in keys:
            data = data[key]
    except (KeyError, TypeError, IndexError):
        data = default
    return data


def get_localized_value(data: Mapping[str, Any], key: str) -> str:
    """Extract localized text field from LinkedIn profile response."""
    lang = dict_gets(data, k=f"{key}|preferredLocale|language", default="en")
    country = dict_gets(data, k=f"{key}|preferredLocale|country", default="US")
    locale = f"{lang}_{country}"
    return str(dict_gets(data, k=f"{key}|localized|{locale}", default=""))


def get_email_address(data: Mapping[str, Any]) -> str:
    """Extract user primary email from LinkedIn emailAddress API response."""
    email = ""
    emails = dict_gets(data, k="elements", default=[])
    if isinstance(emails, list) and emails:
        for e in emails:
            email = str(dict_gets(e, k="handle~|emailAddress", default=""))
            if email:
                break
    elif isinstance(emails, dict):
        email = str(dict_gets(emails, k="handle~|emailAddress", default=""))
    return email


def retrieve_user_from_linkedin(response: Mapping[str, Any]) -> model.User:
    """Retrieve existing user by LinkedIn auth ID or create a new user entity."""
    auth_id = f"linkedin_{response['id']}"
    user_db = model.User.get_by("auth_ids", auth_id)
    if user_db:
        return user_db
    name = " ".join(
        [
            get_localized_value(response, "firstName"),
            get_localized_value(response, "lastName"),
        ]
    ).strip()
    email_response = linkedin.get("emailAddress?q=members&projection=(elements*(handle~))")
    email = get_email_address(email_response.json())
    return auth.create_user_db(
        auth_id=auth_id,
        name=name,
        username=email or name,
        email=email,
        verified=bool(email),
    )
