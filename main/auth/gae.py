"""Google App Engine Users API authentication handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flask
from google.appengine.api import users

import auth
import model
import util
from main import app


if TYPE_CHECKING:
    from werkzeug.wrappers import Response as WerkzeugResponse


@app.route("/signin/gae/")
def signin_gae() -> WerkzeugResponse:
    """Initiate sign-in via App Engine users service."""
    auth.save_request_params()
    gae_url = users.create_login_url(flask.url_for("gae_authorized"))
    return flask.redirect(gae_url)


@app.route("/api/auth/callback/gae/")
def gae_authorized() -> WerkzeugResponse:
    """Handle App Engine users authentication callback."""
    gae_user = users.get_current_user()
    if gae_user is None:
        flask.flash("You denied the request to sign in.")
        return flask.redirect(util.get_next_url())

    user_db = retrieve_user_from_gae(gae_user)
    return auth.signin_user_db(user_db)


def retrieve_user_from_gae(gae_user: users.User) -> model.User:
    """Retrieve existing user by GAE federated ID or create a new user."""
    auth_id = f"federated_{gae_user.user_id()}"
    user_db = model.User.get_by("auth_ids", auth_id)
    if user_db:
        if not user_db.admin and users.is_current_user_admin():
            user_db.admin = True
            user_db.put()
        return user_db

    return auth.create_user_db(
        auth_id=auth_id,
        name=util.create_name_from_email(gae_user.email()),
        username=gae_user.email(),
        email=gae_user.email(),
        verified=True,
        admin=users.is_current_user_admin(),
    )
