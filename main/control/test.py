"""Testing and diagnostic admin handlers."""

import flask
import flask_wtf
import wtforms
from opentelemetry import trace

import auth
import util
from main import app

from . import versions


TESTS = [
    "alert",
    "badge",
    "button",
    "filter",
    "font",
    "form",
    "grid",
    "heading",
    "label",
    "pageres",
    "pagination",
    "paragraph",
    "responsive",
    "social",
    "table",
    "versions",
]

tracer = trace.get_tracer(__name__)


class TestForm(flask_wtf.FlaskForm):
    """Form for testing various WTForms fields and widgets."""

    name = wtforms.StringField(
        "Text",
        [wtforms.validators.DataRequired()],
        filters=[util.strip_filter],
        description="This is a very important field",
    )
    number = wtforms.IntegerField("Integer", [wtforms.validators.Optional()])
    email = wtforms.StringField(
        "Email",
        [wtforms.validators.Optional(), wtforms.validators.Email()],
        filters=[util.email_filter],
    )
    date = wtforms.DateField("Date", [wtforms.validators.Optional()])
    datetime = wtforms.DateTimeField("Date/time", [wtforms.validators.Optional()])
    textarea = wtforms.TextAreaField("Textarea")
    boolean = wtforms.BooleanField(
        "Render it as Markdown",
        [wtforms.validators.Optional()],
    )
    password = wtforms.PasswordField(
        "Password",
        [wtforms.validators.Optional(), wtforms.validators.Length(min=6)],
    )
    password_visible = wtforms.StringField(
        "Password visible",
        [wtforms.validators.Optional(), wtforms.validators.Length(min=6)],
        description="Visible passwords for the win!",
    )
    prefix = wtforms.StringField("Prefix", [wtforms.validators.Optional()])
    suffix = wtforms.StringField("Suffix", [wtforms.validators.DataRequired()])
    both = wtforms.IntegerField("Both", [wtforms.validators.DataRequired()])
    select = wtforms.SelectField(
        "Language",
        [wtforms.validators.Optional()],
        choices=[(s, s.title()) for s in ["english", "greek", "spanish"]],
    )
    checkboxes = wtforms.SelectMultipleField(
        "User permissions",
        [wtforms.validators.DataRequired()],
        choices=[(c, c.title()) for c in ["admin", "moderator", "slave"]],
    )
    radios = wtforms.SelectField(
        "Choose your weapon",
        [wtforms.validators.Optional()],
        choices=[(r, r.title()) for r in ["gun", "knife", "chainsaw", "sword"]],
    )
    public = wtforms.StringField("Public Key", [wtforms.validators.Optional()])
    private = wtforms.StringField("Private Key", [wtforms.validators.Optional()])
    recaptcha = flask_wtf.RecaptchaField()


@app.route("/admin/test/<test>/", methods=["GET", "POST"])
@app.route("/admin/test/", methods=["GET", "POST"])
@auth.admin_required
def admin_test(test: str | None = None) -> str:
    """Render admin diagnostic test views and form components."""
    if test and test not in TESTS:
        flask.abort(404)
    with tracer.start_as_current_span("form_test"):
        form = TestForm()
    if form.validate_on_submit():
        pass

    return flask.render_template(
        "admin/test/test_one.html" if test else "admin/test/test.html",
        title=f"Test: {test.title()}" if test else "Test",
        html_class="test",
        form=form,
        test=test,
        tests=TESTS,
        versions=versions.get_versions(),
        back_url_for="admin_test" if test else None,
    )
