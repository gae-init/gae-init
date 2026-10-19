"""User profile views and settings handlers."""

import flask
import flask_wtf
import werkzeug
import wtforms
from opentelemetry import trace

import auth
import config
import model
import task
import util
from main import app


tracer = trace.get_tracer(__name__)


###############################################################################
# Profile View
###############################################################################
@app.route("/profile/")
@auth.login_required
def profile() -> str:
    """Render the user profile view."""
    user_db = auth.current_user_db()

    return flask.render_template(
        "profile/profile.html",
        title=user_db.name,
        html_class="profile-view",
        user_db=user_db,
    )


###############################################################################
# Profile Update
###############################################################################
class ProfileUpdateForm(flask_wtf.FlaskForm):
    """Form for updating user profile information."""

    name = wtforms.StringField(
        model.User.name._verbose_name,  # noqa: SLF001
        [wtforms.validators.DataRequired()],
        filters=[util.strip_filter],
    )
    email = wtforms.StringField(
        model.User.email._verbose_name,  # noqa: SLF001
        [wtforms.validators.Optional(), wtforms.validators.Email()],
        filters=[util.email_filter],
    )


@app.route("/profile/update/", methods=["GET", "POST"])
@auth.login_required
def profile_update() -> werkzeug.Response | str:
    """Handle profile update form submissions."""
    user_db = auth.current_user_db()

    form = ProfileUpdateForm(obj=user_db)

    if form.validate_on_submit():
        email = form.email.data
        if (
            email
            and not user_db.is_email_available(email, user_db.key)
            and isinstance(form.email.errors, list)
        ):
            form.email.errors.append("This email is already taken.")

        if not form.errors:
            send_verification = not user_db.token or user_db.email != email
            form.populate_obj(user_db)
            if send_verification:
                user_db.verified = False
                task.verify_email_notification(user_db)
            with tracer.start_as_current_span("db_save_user") as span:
                user_db.put()
                span.set_attribute("app.user_id", value=user_db.key.id())
            return flask.redirect(flask.url_for("profile"))

    return flask.render_template(
        "profile/profile_update.html",
        title=user_db.name,
        html_class="profile-update",
        form=form,
        user_db=user_db,
    )


###############################################################################
# Profile Password
###############################################################################
class ProfilePasswordForm(flask_wtf.FlaskForm):
    """Form for changing user password."""

    old_password = wtforms.StringField(
        "Old Password",
        [wtforms.validators.DataRequired()],
    )
    new_password = wtforms.StringField(
        "New Password", [wtforms.validators.DataRequired(), wtforms.validators.Length(min=6)]
    )


@app.route("/profile/password/", methods=["GET", "POST"])
@auth.login_required
def profile_password() -> werkzeug.Response | str:
    """Handle password change form submissions."""
    if not config.CONFIG_DB.has_email_authentication:
        flask.abort(418)
    with tracer.start_as_current_span("db_fetch_user") as span:
        user_db = auth.current_user_db()
        span.set_attribute("app.user_id", value=user_db.key.id())

    form = ProfilePasswordForm(obj=user_db)

    if not user_db.password_hash:
        del form.old_password

    if form.validate_on_submit():
        errors = False
        old_password = form.old_password.data if form.old_password else None
        new_password = form.new_password.data
        if new_password or old_password:
            if (
                user_db.password_hash
                and util.password_hash(user_db, old_password) != user_db.password_hash
                and isinstance(form.old_password.errors, list)
            ):
                form.old_password.errors.append("Invalid current password")
                errors = True

            if not (form.errors or errors):
                user_db.password_hash = util.password_hash(user_db, new_password)
                flask.flash("Your password has been changed.", category="success")

        if not (form.errors or errors):
            with tracer.start_as_current_span("db_save_user") as span:
                user_db.put()
                span.set_attribute("app.user_id", value=user_db.key.id())
            return flask.redirect(flask.url_for("profile"))

    return flask.render_template(
        "profile/profile_password.html",
        title=user_db.name,
        html_class="profile-password",
        form=form,
        user_db=user_db,
    )
