"""Administration controllers and settings configuration views."""

import importlib

import flask
import flask_wtf
import werkzeug
import wtforms
from opentelemetry import trace

import auth
import config
import model
import util
from main import app


tracer = trace.get_tracer(__name__)


###############################################################################
# Admin Stuff
###############################################################################
@app.route("/admin/")
@auth.admin_required
def admin() -> str:
    """Render the main admin control panel."""
    localhost = None
    if config.DEVELOPMENT and ":" in flask.request.host:
        try:
            parts = flask.request.host.split(":")
            port = int(parts[1]) + 1
            localhost = f"http://{parts[0]}:{port}/"
        except (IndexError, ValueError):
            pass

    return flask.render_template(
        "admin/admin.html",
        title="Admin",
        html_class="admin",
        localhost=localhost,
    )


###############################################################################
# Config Stuff
###############################################################################
class ConfigUpdateForm(flask_wtf.FlaskForm):
    """Form for updating core application configuration settings."""

    analytics_id = wtforms.StringField(
        model.Config.analytics_id._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    announcement_html = wtforms.TextAreaField(
        model.Config.announcement_html._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    announcement_type = wtforms.SelectField(
        model.Config.announcement_type._verbose_name,  # noqa: SLF001
        choices=[(t, t.title()) for t in model.Config.announcement_type._choices],  # noqa: SLF001
    )
    anonymous_recaptcha = wtforms.BooleanField(
        model.Config.anonymous_recaptcha._verbose_name,  # noqa: SLF001
    )
    brand_name = wtforms.StringField(
        model.Config.brand_name._verbose_name,  # noqa: SLF001
        [wtforms.validators.DataRequired()],
        filters=[util.strip_filter],
    )
    check_unique_email = wtforms.BooleanField(
        model.Config.check_unique_email._verbose_name,  # noqa: SLF001
    )
    email_authentication = wtforms.BooleanField(
        model.Config.email_authentication._verbose_name,  # noqa: SLF001
    )
    feedback_email = wtforms.StringField(
        model.Config.feedback_email._verbose_name,  # noqa: SLF001
        [wtforms.validators.Optional(), wtforms.validators.Email()],
        filters=[util.email_filter],
    )
    flask_secret_key = wtforms.StringField(
        model.Config.flask_secret_key._verbose_name,  # noqa: SLF001
        [wtforms.validators.Optional()],
        filters=[util.strip_filter],
    )
    notify_on_new_user = wtforms.BooleanField(
        model.Config.notify_on_new_user._verbose_name,  # noqa: SLF001
    )
    recaptcha_private_key = wtforms.StringField(
        model.Config.recaptcha_private_key._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    recaptcha_public_key = wtforms.StringField(
        model.Config.recaptcha_public_key._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    salt = wtforms.StringField(
        model.Config.salt._verbose_name,  # noqa: SLF001
        [wtforms.validators.Optional()],
        filters=[util.strip_filter],
    )
    trusted_hosts = wtforms.StringField(
        model.Config.trusted_hosts._verbose_name,  # noqa: SLF001
        [wtforms.validators.Optional()],
        description="Comma separated: 127.0.0.1, example.com, etc",
    )
    verify_email = wtforms.BooleanField(
        model.Config.verify_email._verbose_name,  # noqa: SLF001
    )


@app.route("/admin/config/", methods=["GET", "POST"])
@auth.admin_required
def admin_config() -> werkzeug.Response | str:
    """Handle application configuration form updates."""
    with tracer.start_as_current_span("db_fetch_config"):
        config_db = model.Config.get_master_db()

    form = ConfigUpdateForm(obj=config_db)
    if form.validate_on_submit():
        if form.trusted_hosts.data:
            form.trusted_hosts.data = {e.strip() for e in form.trusted_hosts.data.split(",")}
        else:
            form.trusted_hosts.data = []
        form.populate_obj(config_db)
        if not config_db.flask_secret_key:
            config_db.flask_secret_key = util.uuid()
        if not config_db.salt:
            config_db.salt = util.uuid()

        with tracer.start_as_current_span("db_save_config"):
            config_db.put()

        with tracer.start_as_current_span("reload_config"):
            importlib.reload(config)
            app.config.update(CONFIG_DB=config_db)
        return flask.redirect(flask.url_for("admin"))
    form.trusted_hosts.data = ", ".join(config_db.trusted_hosts)

    return flask.render_template(
        "admin/admin_config.html",
        title="App Config",
        html_class="admin-config",
        form=form,
        api_url=flask.url_for("api.admin.config"),
    )


###############################################################################
# Auth Stuff
###############################################################################
class AuthUpdateForm(flask_wtf.FlaskForm):
    """Form for updating OAuth and third-party authentication credentials."""

    bitbucket_key = wtforms.StringField(
        model.Config.bitbucket_key._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    bitbucket_secret = wtforms.StringField(
        model.Config.bitbucket_secret._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    facebook_app_id = wtforms.StringField(
        model.Config.facebook_app_id._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    facebook_app_secret = wtforms.StringField(
        model.Config.facebook_app_secret._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    github_client_id = wtforms.StringField(
        model.Config.github_client_id._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    github_client_secret = wtforms.StringField(
        model.Config.github_client_secret._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    google_client_id = wtforms.StringField(
        model.Config.google_client_id._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    google_client_secret = wtforms.StringField(
        model.Config.google_client_secret._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    linkedin_api_key = wtforms.StringField(
        model.Config.linkedin_api_key._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    linkedin_secret_key = wtforms.StringField(
        model.Config.linkedin_secret_key._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    microsoft_client_id = wtforms.StringField(
        model.Config.microsoft_client_id._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    microsoft_client_secret = wtforms.StringField(
        model.Config.microsoft_client_secret._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    twitter_consumer_key = wtforms.StringField(
        model.Config.twitter_consumer_key._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )
    twitter_consumer_secret = wtforms.StringField(
        model.Config.twitter_consumer_secret._verbose_name,  # noqa: SLF001
        filters=[util.strip_filter],
    )


@app.route("/admin/auth/", methods=["GET", "POST"])
@auth.admin_required
def admin_auth() -> werkzeug.Response | str:
    """Handle OAuth authentication settings form updates."""
    with tracer.start_as_current_span("db_fetch_config"):
        config_db = model.Config.get_master_db()
    form = AuthUpdateForm(obj=config_db)
    if form.validate_on_submit():
        form.populate_obj(config_db)
        with tracer.start_as_current_span("db_save_config"):
            config_db.put()
        with tracer.start_as_current_span("reload_config"):
            importlib.reload(config)
            app.config.update(CONFIG_DB=config_db)
        return flask.redirect(flask.url_for("admin"))

    return flask.render_template(
        "admin/admin_auth.html",
        title="Auth Config",
        html_class="admin-auth",
        form=form,
        api_url=flask.url_for("api.admin.config"),
    )
