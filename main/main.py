"""Application initialization and configuration."""

import logging
import sys
from datetime import datetime
from typing import Any, cast

import flask
from google.cloud import ndb

import cache
import config
import util
from api import helpers
from telemetry import setup_opentelemetry


# route logging output to stdout with severity levels included
logging.basicConfig(
    stream=sys.stdout, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


class GaeRequest(flask.Request):
    """Custom Flask Request that enforces trusted hosts."""

    trusted_hosts = getattr(config, "TRUSTED_HOSTS", [])


# Flask application initialization
app = flask.Flask(__name__, static_folder="static", static_url_path="/p")
app.config.from_object(config)
app.request_class = GaeRequest if getattr(config, "TRUSTED_HOSTS", None) else flask.Request

# Jinja2 template configuration
app.jinja_env.line_statement_prefix = "#"
app.jinja_env.line_comment_prefix = "##"
cast("dict[str, Any]", app.jinja_env.globals).update(
    check_form_fields=util.check_form_fields,
    datetime=datetime,
    is_iterable=util.is_iterable,
    slugify=util.slugify,
    update_query_argument=util.update_query_argument,
)

# add telemetry
setup_opentelemetry(app)

ndb_client = ndb.Client()


# NDB Context Lifecycle Hooks (replaces WSGI Middleware)
@app.before_request
def enter_ndb_context() -> None:
    """Enter NDB context prior to route handling, API execution, and template rendering."""
    ctx = ndb_client.context(global_cache=cache.get_ndb_global_cache())
    flask.g.ndb_context_manager = ctx
    ctx.__enter__()


@app.teardown_request
def exit_ndb_context(exception: BaseException | None = None) -> None:
    """Safely close NDB context and flush L1 memory after request completion."""
    ctx = flask.g.pop("ndb_context_manager", None)
    if ctx is not None:
        exc_type = type(exception) if exception else None
        ctx.__exit__(exc_type, exception, exception.__traceback__ if exception else None)


# route and signal registration must occur after `app` is defined
import auth  # noqa: E402, F401
import control  # noqa: E402, F401
import model  # noqa: E402, F401
import task  # noqa: E402, F401


api_v1 = helpers.Api(app, prefix="/api/v1")

# API resource registration must occur after `api_v1` is defined
import api.v1  # noqa: E402, F401, I001

# enable App Engine Bundled Services and Debugger setup
if config.DEVELOPMENT:
    from google.appengine.ext import testbed
    from werkzeug import debug

    # configure logging for local development/testing
    logging.getLogger().setLevel(logging.DEBUG)

    tb = testbed.Testbed()
    tb.setup_env(app_id="gae-init")
    tb.activate()
    tb.init_user_stub(login_url="/_ah/login?continue=%s", logout_url="/_ah/logout?continue=%s")
    tb.init_memcache_stub()
    tb.init_mail_stub()
    tb.init_app_identity_stub()
    try:
        cast("Any", app).wsgi_app = debug.DebuggedApplication(
            app.wsgi_app,
            evalex=True,
            pin_security=False,
        )
    except TypeError:
        cast("Any", app).wsgi_app = debug.DebuggedApplication(app.wsgi_app, evalex=True)
    # enable interactive browser debugger to spot unhandled exceptions
    app.testing = False

else:
    from google.appengine.api import wrap_wsgi_app

    cast("Any", app).wsgi_app = wrap_wsgi_app(app.wsgi_app)
