import hashlib

from google.cloud import ndb
from webargs import fields as wf
from webargs.flaskparser import parser

import config
import model
import util
from api import fields


class User(model.Base):
    name = ndb.StringProperty(required=True)
    username = ndb.StringProperty(required=True)
    email = ndb.StringProperty(default="")
    auth_ids = ndb.StringProperty(repeated=True)
    active = ndb.BooleanProperty(default=True)
    admin = ndb.BooleanProperty(default=False)
    permissions = ndb.StringProperty(repeated=True)
    verified = ndb.BooleanProperty(default=False)
    token = ndb.StringProperty(default="")
    password_hash = ndb.StringProperty(default="")

    def has_permission(self, perm):
        return self.admin or perm in self.permissions

    def avatar_url_size(self, size: int | None = None) -> str:
        """Return the user's Gravatar URL, optionally using given size."""
        email_or_user = (self.email or self.username).strip().lower().encode("utf-8")
        email_hash = hashlib.sha256(email_or_user).hexdigest()
        size_param = f"&s={size}" if size and size > 0 else ""
        return f"https://gravatar.com/avatar/{email_hash}?d=identicon{size_param}"

    avatar_url = property(avatar_url_size)

    @classmethod
    def get_dbs(cls, admin=None, active=None, verified=None, permissions=None, **kwargs):
        args = parser.parse(
            {
                "admin": wf.Bool(load_default=None),
                "active": wf.Bool(load_default=None),
                "verified": wf.Bool(load_default=None),
                "permissions": wf.DelimitedList(wf.Str(), delimiter=",", load_default=[]),
            },
            location="query",
        )
        return super().get_dbs(
            admin=admin or args["admin"],
            active=active or args["active"],
            verified=verified or args["verified"],
            permissions=permissions or args["permissions"],
            **kwargs,
        )

    @classmethod
    def is_username_available(cls, username, self_key=None):
        if self_key is None:
            return cls.get_by("username", username) is None
        user_keys, _ = util.get_keys(cls.query(), username=username, limit=2)
        return not user_keys or (self_key in user_keys and not user_keys[1:])

    @classmethod
    def is_email_available(cls, email, self_key=None):
        if not config.CONFIG_DB.check_unique_email:
            return True
        user_keys, _ = util.get_keys(
            cls.query(),
            email=email,
            verified=True,
            limit=2,
        )
        return not user_keys or (self_key in user_keys and not user_keys[1:])

    FIELDS = {
        "active": fields.Boolean,
        "admin": fields.Boolean,
        "auth_ids": fields.List(fields.String),
        "avatar_url": fields.String,
        "email": fields.String,
        "name": fields.String,
        "permissions": fields.List(fields.String),
        "username": fields.String,
        "verified": fields.Boolean,
    }

    FIELDS.update(model.Base.FIELDS)
