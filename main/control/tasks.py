"""Background task handlers for Cloud Tasks."""

import logging

import flask
from google.appengine.api import mail

import config
from main import app


logger = logging.getLogger(__name__)


###############################################################################
# Background Task Handlers
###############################################################################


@app.route("/_tasks/send_mail", methods=["POST"])
def task_send_mail() -> tuple[str, int]:
    """Send an email via GAE Mail API from a Cloud Tasks payload."""
    # only allow requests from Cloud Tasks or local development
    queue_name = flask.request.headers.get("X-Appengine-Queuename")
    if not config.DEVELOPMENT and not queue_name:
        logger.warning("Unauthorized task execution attempt.")
        flask.abort(403)

    payload = flask.request.get_json()
    if not payload:
        flask.abort(400, "Missing JSON payload")

    try:
        mail.send_mail(**payload)
    except Exception:
        logger.exception("Error sending mail from task")
        flask.abort(500)
    else:
        return "OK", 200
