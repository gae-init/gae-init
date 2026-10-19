from google.cloud import ndb

import config
import model
import util
from api import fields


class Config(model.Base, model.ConfigAuth):
    analytics_id = ndb.TextProperty(default="", verbose_name="Measurement ID")
    announcement_html = ndb.TextProperty(default="", verbose_name="Announcement HTML")
    announcement_type = ndb.TextProperty(
        default="info", choices=["info", "warning", "success", "danger"]
    )
    anonymous_recaptcha = ndb.BooleanProperty(
        default=False, verbose_name="Use reCAPTCHA in forms for unauthorized users"
    )
    brand_name = ndb.TextProperty(default=config.APPLICATION_ID)
    check_unique_email = ndb.BooleanProperty(
        default=True, verbose_name="Check for uniqueness of the verified emails"
    )
    email_authentication = ndb.BooleanProperty(
        default=False, verbose_name="Email authentication for sign in/sign up"
    )
    feedback_email = ndb.TextProperty(default="")
    flask_secret_key = ndb.TextProperty(default=util.uuid())
    notify_on_new_user = ndb.BooleanProperty(
        default=True, verbose_name="Send an email notification when a user signs up"
    )
    recaptcha_private_key = ndb.TextProperty(default="", verbose_name="Private Key")
    recaptcha_public_key = ndb.TextProperty(default="", verbose_name="Public Key")
    salt = ndb.TextProperty(default=util.uuid())
    trusted_hosts = ndb.TextProperty(repeated=True, verbose_name="Trusted Hosts")
    verify_email = ndb.BooleanProperty(default=True, verbose_name="Verify user emails")

    @property
    def has_anonymous_recaptcha(self):
        return bool(self.anonymous_recaptcha and self.has_recaptcha)

    @property
    def has_email_authentication(self):
        return bool(self.email_authentication and self.feedback_email and self.verify_email)

    @property
    def has_recaptcha(self):
        return bool(self.recaptcha_private_key and self.recaptcha_public_key)

    @classmethod
    def get_master_db(cls):
        return cls.get_or_insert("master")

    FIELDS = {
        "analytics_id": fields.String,
        "announcement_html": fields.String,
        "announcement_type": fields.String,
        "anonymous_recaptcha": fields.Boolean,
        "brand_name": fields.String,
        "check_unique_email": fields.Boolean,
        "email_authentication": fields.Boolean,
        "feedback_email": fields.String,
        "flask_secret_key": fields.String,
        "notify_on_new_user": fields.Boolean,
        "recaptcha_private_key": fields.String,
        "recaptcha_public_key": fields.String,
        "salt": fields.String,
        "trusted_hosts": fields.List(fields.String),
        "verify_email": fields.Boolean,
    }

    FIELDS.update(model.Base.FIELDS)
    FIELDS.update(model.ConfigAuth.FIELDS)
