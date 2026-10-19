"""User administration API resources for v1 endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flask
import flask_restful
from google.cloud import ndb

import auth
import model
import util
from api import helpers
from main import api_v1


if TYPE_CHECKING:
    from collections.abc import Sequence


@api_v1.resource("/admin/user/", endpoint="api.admin.user.list")
class AdminUserListAPI(flask_restful.Resource):
    """Resource for querying and bulk-deleting users."""

    @auth.admin_required
    def get(self) -> flask.Response:
        """Return list of users matching query or specified keys."""
        user_keys = util.param("user_keys", list)
        if user_keys:
            user_db_keys = [ndb.Key(urlsafe=k) for k in user_keys]
            user_dbs = ndb.get_multi(user_db_keys)
            return helpers.make_response(user_dbs, model.User.FIELDS)

        user_dbs, cursors = model.User.get_dbs(prev_cursor=True)
        return helpers.make_response(user_dbs, model.User.FIELDS, cursors)

    @auth.admin_required
    def delete(self) -> flask.Response:
        """Delete multiple users specified by urlsafe keys."""
        user_keys = util.param("user_keys", list)
        if not user_keys:
            helpers.make_not_found_exception(f"User(s) {user_keys} not found")
        user_db_keys = [ndb.Key(urlsafe=k) for k in user_keys]
        delete_user_dbs(user_db_keys)
        return flask.jsonify(
            {
                "result": user_keys,
                "status": "success",
            }
        )


@api_v1.resource("/admin/user/<string:user_key>/", endpoint="api.admin.user")
class AdminUserAPI(flask_restful.Resource):
    """Resource for individual user inspection and deletion."""

    @auth.admin_required
    def get(self, user_key: str) -> flask.Response:
        """Retrieve and return a single user by urlsafe key."""
        user_db = ndb.Key(urlsafe=user_key).get()
        if not user_db:
            helpers.make_not_found_exception(f"User {user_key} not found")
        return helpers.make_response(user_db, model.User.FIELDS)

    @auth.admin_required
    def delete(self, user_key: str) -> flask.Response:
        """Delete a single user by urlsafe key."""
        user_db = ndb.Key(urlsafe=user_key).get()
        if not user_db:
            helpers.make_not_found_exception(f"User {user_key} not found")
        delete_user_dbs([user_db.key])
        return helpers.make_response(user_db, model.User.FIELDS)


###############################################################################
# Helpers
###############################################################################
@ndb.transactional(xg=True)
def delete_user_dbs(user_db_keys: Sequence[ndb.Key]) -> None:
    """Delete multiple user entities transactionally across groups."""
    ndb.delete_multi(user_db_keys)
