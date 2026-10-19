"""Background tasks and notification handlers."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import flask
from google.appengine.api import taskqueue

import config
import util


if TYPE_CHECKING:
    from collections.abc import Mapping

    import model


logger = logging.getLogger(__name__)


###############################################################################
# Helpers
###############################################################################
def enqueue_task(
    url: str,
    payload: Mapping[str, object],
    queue_name: str = "background",
) -> None:
    """Enqueue a background task onto Google App Engine taskqueue."""
    if config.DEVELOPMENT:
        logger.info(
            "Development mode: task simulated for %s (queue=%s)",
            url,
            queue_name,
        )
        if url == "/_tasks/send_mail":
            logger.info(
                "Development simulated email:\nTo: %s\nSubject: %s\nBody:\n%s",
                payload.get("to"),
                payload.get("subject"),
                payload.get("body"),
            )
        else:
            logger.info("Payload: %s", json.dumps(dict(payload), indent=2))
        return

    try:
        taskqueue.add(
            url=url,
            payload=json.dumps(dict(payload)),
            queue_name=queue_name,
            headers={"Content-Type": "application/json"},
        )
    except Exception:
        logger.exception("Failed to enqueue task")


def send_mail_notification(
    subject: str,
    body: str,
    to: str | None = None,
    **kwargs: object,
) -> None:
    """Enqueue an email notification background task."""
    if not config.CONFIG_DB.feedback_email:
        return
    brand_name = config.CONFIG_DB.brand_name
    sender = f"{brand_name} <{config.CONFIG_DB.feedback_email}>"
    full_subject = f"[{brand_name}] {subject}"

    payload: dict[str, object] = {
        "sender": sender,
        "to": to or sender,
        "subject": full_subject,
        "body": body,
    }
    payload.update(kwargs)
    enqueue_task("/_tasks/send_mail", payload)


###############################################################################
# Admin Notifications
###############################################################################
def new_user_notification(user_db: model.User) -> None:
    """Notify administrator about a new user registration."""
    if not config.CONFIG_DB.notify_on_new_user:
        return
    auth_ids_str = "".join(f"{': '.join(a.split('_'))}\n" for a in user_db.auth_ids)
    user_url = flask.url_for("user_update", user_id=user_db.key.id(), _external=True)
    body = (
        f"name: {user_db.name}\n"
        f"username: {user_db.username}\n"
        f"email: {user_db.email}\n"
        f"{auth_ids_str}\n"
        f"{user_url}"
    )
    send_mail_notification(f"New user: {user_db.name}", body)


###############################################################################
# User Related
###############################################################################
def verify_email_notification(user_db: model.User) -> None:
    """Send an email verification link to the user."""
    if not (config.CONFIG_DB.verify_email and user_db.email) or user_db.verified:
        return
    user_db.token = util.uuid()
    user_db.put()

    to = f"{user_db.name} <{user_db.email}>"
    verify_url = flask.url_for("user_verify", token=user_db.token, _external=True)
    brand = config.CONFIG_DB.brand_name
    body = f"""Hello {user_db.name},

It seems someone (hopefully you) tried to verify your email with {brand}.

If it was you, please verify it by following this link:

{verify_url}

If it wasn't you, we apologize. You can either ignore this email or reply to it
so we can take a look.

Best regards,
{brand}
"""

    flask.flash(
        "A verification link has been sent to your email address.",
        category="success",
    )
    send_mail_notification("Verify your email.", body, to)


def reset_password_notification(user_db: model.User) -> None:
    """Send a password reset link to the user."""
    if not user_db.email:
        return
    user_db.token = util.uuid()
    user_db.put()

    to = f"{user_db.name} <{user_db.email}>"
    reset_url = flask.url_for("user_reset", token=user_db.token, _external=True)
    brand = config.CONFIG_DB.brand_name
    body = f"""Hello {user_db.name},

It seems someone (hopefully you) tried to reset your password with {brand}.

If it was you, please reset it by following this link:

{reset_url}

If it wasn't you, we apologize. You can either ignore this email or reply to it
so we can take a look.

Best regards,
{brand}
"""

    flask.flash(
        "A reset link has been sent to your email address.",
        category="success",
    )
    send_mail_notification("Reset your password", body, to)


def activate_user_notification(user_db: model.User) -> None:
    """Send an account activation link to a newly created user."""
    if not user_db.email:
        return
    user_db.token = util.uuid()
    user_db.put()

    to = user_db.email
    activate_url = flask.url_for("user_activate", token=user_db.token, _external=True)
    brand = config.CONFIG_DB.brand_name
    body = f"""Welcome to {brand}.

Follow the link below to confirm your email address and activate your account:

{activate_url}

If it wasn't you, we apologize. You can either ignore this email or reply to it
so we can take a look.

Best regards,
{brand}
"""

    flask.flash(
        "An activation link has been sent to your email address.",
        category="success",
    )
    send_mail_notification("Activate your account", body, to)


###############################################################################
# Admin Related
###############################################################################
def email_conflict_notification(email: str) -> None:
    """Notify administrator about an email conflict in user accounts."""
    user_list_url = flask.url_for("user_list", email=email, _external=True)
    body = f"There is a conflict with {email}\n\n{user_list_url}"
    send_mail_notification(f"Conflict with: {email}", body)
