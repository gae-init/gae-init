"""Welcome and general route handlers."""

import flask

import cache
import config
from main import app


###############################################################################
# Warmup request
###############################################################################
@app.route("/_ah/warmup")
def warmup() -> str:
    """Handle App Engine warmup requests."""
    cache.get_redis_client()
    return "success"


###############################################################################
# Welcome
###############################################################################
@app.route("/")
def welcome() -> str:
    """Render the welcome page."""
    return flask.render_template("welcome.html", html_class="welcome")


###############################################################################
# Sitemap stuff
###############################################################################
@app.route("/sitemap.xml")
def sitemap() -> flask.Response:
    """Render and serve the sitemap XML."""
    response = flask.make_response(
        flask.render_template(
            "sitemap.xml",
            lastmod=config.CURRENT_VERSION_DATE.strftime("%Y-%m-%d"),
        )
    )
    response.headers["Content-Type"] = "application/xml"
    return response


###############################################################################
# Static/meta files (fallback for local development/testing)
###############################################################################
if config.DEVELOPMENT:

    @app.route("/favicon.ico")
    def local_dev_favicon() -> flask.Response:
        """Serve favicon.ico for local development."""
        return flask.send_from_directory("static/img", "favicon.ico")

    @app.route("/manifest.json")
    def local_dev_manifest() -> flask.Response:
        """Serve manifest.json for local development."""
        return flask.send_from_directory("static", "manifest.json")

    @app.route("/robots.txt")
    def local_dev_robots() -> flask.Response:
        """Serve robots.txt for local development."""
        return flask.send_from_directory("static", "robots.txt")


###############################################################################
# Local development login handlers (fallback for local development/testing)
###############################################################################
if config.DEVELOPMENT:
    import os

    import werkzeug

    @app.route("/_ah/login")
    def local_dev_login() -> werkzeug.Response:
        """Log in as a mock user for local development and redirect."""
        continue_url = flask.request.args.get("continue", "/")
        os.environ["USER_EMAIL"] = "test@example.com"
        os.environ["USER_ID"] = "test-123"
        os.environ["USER_IS_ADMIN"] = "1"
        return flask.redirect(continue_url)

    @app.route("/_ah/logout")
    def local_dev_logout() -> werkzeug.Response:
        """Log out mock user for local development and redirect."""
        continue_url = flask.request.args.get("continue", "/")
        os.environ.pop("USER_EMAIL", None)
        os.environ.pop("USER_ID", None)
        os.environ.pop("USER_IS_ADMIN", None)
        return flask.redirect(continue_url)
