"""Error handlers for HTTP and application exceptions."""

import http
import logging

import flask
import werkzeug
import werkzeug.exceptions

import config
from api import helpers
from main import app


logger = logging.getLogger(__name__)


@app.errorhandler(400)  # Bad Request
@app.errorhandler(401)  # Unauthorized
@app.errorhandler(403)  # Forbidden
@app.errorhandler(404)  # Not Found
@app.errorhandler(405)  # Method Not Allowed
@app.errorhandler(409)  # Conflict
@app.errorhandler(410)  # Gone
@app.errorhandler(418)  # I'm a Teapot
@app.errorhandler(422)  # Unprocessable Entity
@app.errorhandler(500)  # Internal Server Error
def error_handler(e: Exception) -> tuple[flask.Response | str, int]:
    """Render an error page or return JSON error response for API routes."""
    code = getattr(e, "code", 500)
    error_name = getattr(e, "name", "Internal Server Error")
    logger.error("%d - %s: %s", code, error_name, flask.request.url)
    if code != http.HTTPStatus.NOT_FOUND:
        logger.error("Exception handled: %s", e, exc_info=e)

    if flask.request.path.startswith("/api/"):
        return helpers.handle_error(e)

    return (
        flask.render_template(
            "error.html",
            title=f"Error {code} ({error_name})!!1",
            html_class="error-page",
            error=e,
        ),
        code,
    )


if config.PRODUCTION:

    @app.errorhandler(Exception)
    def production_error_handler(
        e: Exception,
    ) -> werkzeug.exceptions.HTTPException | tuple[flask.Response | str, int]:
        """Handle exceptions in production, passing through 301 and 302 redirects."""
        if isinstance(e, werkzeug.exceptions.HTTPException) and e.code in (301, 302):
            return e
        return error_handler(e)
