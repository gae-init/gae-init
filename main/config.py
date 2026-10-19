"""Application configuration settings for App Engine environments."""

import os

import google.auth


# In GAE Py3, GAE_ENV is set to "standard" (in Py2, SERVER_SOFTWARE was set)
PRODUCTION = os.environ.get("GAE_ENV") == "standard" or os.environ.get(
    "SERVER_SOFTWARE", ""
).startswith("Google App Eng")
DEBUG = DEVELOPMENT = not PRODUCTION

_, PROJECT_ID = google.auth.default()
try:
    # This part is surrounded in try/except in case the config.py file is
    # also used in other scripts that are not aware of the GAE target
    APPLICATION_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not APPLICATION_ID:
        from google.appengine.api import app_identity

        APPLICATION_ID = app_identity.get_application_id()
except (ImportError, AttributeError):
    APPLICATION_ID = "Testing"

else:
    from datetime import UTC, datetime

    # GAE_VERSION is used in Py3, CURRENT_VERSION_ID was used in Py2
    CURRENT_VERSION_ID = (
        os.environ.get("GAE_VERSION") or os.environ.get("CURRENT_VERSION_ID") or APPLICATION_ID
    )
    CURRENT_VERSION_NAME = CURRENT_VERSION_ID.split(".")[0]

    if DEVELOPMENT:
        CURRENT_VERSION_TIMESTAMP = int(datetime.now(UTC).timestamp())
    else:
        # Py2 GAE versions were in the format "version.timestamp" which required bit-shifting.
        # Py3 GAE versions are usually just the version name.
        _version_parts = CURRENT_VERSION_ID.split(".")
        if len(_version_parts) > 1 and _version_parts[1].isdigit():
            CURRENT_VERSION_TIMESTAMP = int(_version_parts[1]) >> 28
        else:
            CURRENT_VERSION_TIMESTAMP = int(datetime.now(UTC).timestamp())
    # Decoding the CURRENT_VERSION_ID according to:
    # http://stackoverflow.com/questions/14639488
    CURRENT_VERSION_DATE = datetime.fromtimestamp(CURRENT_VERSION_TIMESTAMP, tz=UTC)
    USER_AGENT = f"{APPLICATION_ID}/{CURRENT_VERSION_ID}"
    # minimize JSON in production
    JSONIFY_PRETTYPRINT_REGULAR = not PRODUCTION

    import contextlib

    from google.cloud import ndb

    import model

    try:
        ndb.context.get_context()
        ctx = contextlib.nullcontext()
    except Exception:  # noqa: BLE001
        ctx = ndb.Client().context()

    try:
        with ctx:
            CONFIG_DB = model.Config.get_master_db()
            SECRET_KEY = CONFIG_DB.flask_secret_key.encode("utf-8")
            RECAPTCHA_PUBLIC_KEY = CONFIG_DB.recaptcha_public_key
            RECAPTCHA_PRIVATE_KEY = CONFIG_DB.recaptcha_private_key
            TRUSTED_HOSTS = CONFIG_DB.trusted_hosts
    except Exception:  # noqa: BLE001
        CONFIG_DB = model.Config()

DEFAULT_DB_LIMIT = 100
RECAPTCHA_LIMIT = 8
SIGNIN_RETRY_LIMIT = 4
TAG_SEPARATOR = " "
