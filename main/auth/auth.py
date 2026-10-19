"""Core authentication, session management, and access control decorators."""

from __future__ import annotations

import functools
import re
from typing import TYPE_CHECKING, Any

import flask
import flask_login
import flask_wtf
import unidecode
import wtforms
from authlib.integrations.flask_client import OAuth, OAuthError
from google.cloud import ndb
from opentelemetry import trace

import cache
import config
import model
import task
import util
from main import app


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from werkzeug.wrappers import Response as WerkzeugResponse


_signals = flask.signals.Namespace()

tracer = trace.get_tracer(__name__)


###############################################################################
# Flask Login
###############################################################################
login_manager = flask_login.LoginManager()


class AnonymousUser(flask_login.AnonymousUserMixin):
    """Anonymous user representation with default unprivileged attributes."""

    id = 0
    admin = False
    name = "Anonymous"
    user_db = None

    def key(self) -> str | None:
        """Return None as anonymous users have no datastore key."""
        return None

    def has_permission(self, permission: str) -> bool:  # noqa: ARG002
        """Return False for unauthenticated anonymous users."""
        return False


login_manager.anonymous_user = AnonymousUser  # ty: ignore[invalid-assignment]


class FlaskUser(AnonymousUser):
    """Authenticated user session wrapper around a User datastore entity."""

    user_db: model.User

    def __init__(self, user_db: model.User) -> None:
        """Initialize FlaskUser with the corresponding datastore User entity."""
        self.user_db = user_db
        self.id = user_db.key.id()
        self.name = user_db.name
        self.admin = user_db.admin

    def key(self) -> str:
        """Return URL-safe datastore key string."""
        urlsafe = self.user_db.key.urlsafe()
        return urlsafe.decode("utf-8") if isinstance(urlsafe, bytes) else str(urlsafe)

    def get_id(self) -> str:
        """Return user identifier used by Flask-Login session."""
        urlsafe = self.user_db.key.urlsafe()
        return urlsafe.decode("utf-8") if isinstance(urlsafe, bytes) else str(urlsafe)

    def is_authenticated(self) -> bool:
        """Return True indicating the user is authenticated."""
        return True

    def is_active(self) -> bool:
        """Check whether the user account is active."""
        return bool(self.user_db.active)

    def is_anonymous(self) -> bool:
        """Return False indicating this is an authenticated user."""
        return False

    def has_permission(self, permission: str) -> bool:
        """Check whether user has the specified permission."""
        return bool(self.user_db.has_permission(permission))


@login_manager.user_loader
def load_user(key: str) -> FlaskUser | None:
    """Load user by urlsafe datastore key string."""
    with tracer.start_as_current_span("db_fetch_user") as span:
        span.set_attribute("app.key_param", value=key)
        user_db = ndb.Key(urlsafe=key).get()
        if user_db:
            span.set_attribute("app.user_found", value=True)
            span.set_attribute("app.user_id", value=user_db.key.id())
            return FlaskUser(user_db)
        span.set_attribute("app.user_found", value=False)
    return None


login_manager.init_app(app)


def current_user_id() -> int | str:
    """Return the currently authenticated user's ID or 0 if anonymous."""
    return flask_login.current_user.id


def current_user_key() -> ndb.Key | None:
    """Return the Datastore key of current user or None if anonymous."""
    user = flask_login.current_user
    user_db = getattr(user, "user_db", None)
    return user_db.key if user_db else None


def current_user_db() -> Any:  # noqa: ANN401
    """Return the current user's Datastore model instance or None."""
    return getattr(flask_login.current_user, "user_db", None)


def is_logged_in() -> bool:
    """Check if the current request user is authenticated."""
    return flask_login.current_user.id != 0


###############################################################################
# Decorators
###############################################################################
def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate routes to require an authenticated user session."""
    decorator_order_guard(f, "auth.login_required")

    @functools.wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> Any:  # noqa: ANN401
        if is_logged_in():
            return f(*args, **kwargs)
        if flask.request.path.startswith("/api/"):
            return flask.abort(401)
        return flask.redirect(flask.url_for("signin", next=flask.request.url))

    return decorated_function


def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate routes to require an administrator user session."""
    decorator_order_guard(f, "auth.admin_required")

    @functools.wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> Any:  # noqa: ANN401
        user_db = current_user_db()
        if is_logged_in() and user_db and user_db.admin:
            return f(*args, **kwargs)
        if not is_logged_in() and flask.request.path.startswith("/api/"):
            return flask.abort(401)
        if not is_logged_in():
            return flask.redirect(flask.url_for("signin", next=flask.request.url))
        return flask.abort(403)

    return decorated_function


def cron_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate routes to require an App Engine cron header or admin session."""
    decorator_order_guard(f, "auth.cron_required")

    @functools.wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> Any:  # noqa: ANN401
        if "X-Appengine-Cron" in flask.request.headers:
            return f(*args, **kwargs)
        user_db = current_user_db()
        if is_logged_in() and user_db and user_db.admin:
            return f(*args, **kwargs)
        if not is_logged_in():
            return flask.redirect(flask.url_for("signin", next=flask.request.url))
        return flask.abort(403)

    return decorated_function


permission_registered = _signals.signal("permission-registered")


def permission_required(
    permission: str | None = None,
    methods: Sequence[str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorate routes to require a specific permission for given HTTP methods."""

    def permission_decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        decorator_order_guard(f, "auth.permission_required")

        # default to decorated function name as permission
        perm = permission or getattr(f, "__name__", "permission")
        meths = [m.upper() for m in methods] if methods else None

        permission_registered.send(f, permission=perm)

        @functools.wraps(f)
        def decorated_function(*args: object, **kwargs: object) -> Any:  # noqa: ANN401
            if meths and flask.request.method.upper() not in meths:
                return f(*args, **kwargs)
            user_db = current_user_db()
            if is_logged_in() and user_db and user_db.has_permission(perm):
                return f(*args, **kwargs)
            if not is_logged_in():
                if flask.request.path.startswith("/api/"):
                    return flask.abort(401)
                return flask.redirect(flask.url_for("signin", next=flask.request.url))
            return flask.abort(403)

        return decorated_function

    return permission_decorator


###############################################################################
# Sign in stuff
###############################################################################
class SignInForm(flask_wtf.FlaskForm):
    """Form for user password-based sign-in."""

    email = wtforms.StringField(
        "Email",
        [wtforms.validators.DataRequired()],
        filters=[util.email_filter],
    )
    password = wtforms.StringField(
        "Password",
        [wtforms.validators.DataRequired()],
    )
    remember = wtforms.BooleanField(
        "Keep me signed in",
        [wtforms.validators.Optional()],
    )
    recaptcha = flask_wtf.RecaptchaField()
    next_url = wtforms.HiddenField()


@app.route("/signin/", methods=["GET", "POST"])
def signin() -> WerkzeugResponse | str:
    """Handle user sign-in page rendering and form authentication."""
    next_url = util.get_next_url()
    form = None
    if config.CONFIG_DB.has_email_authentication:
        form = form_with_recaptcha(SignInForm())
        save_request_params()
        if form.validate_on_submit():
            result = get_user_db_from_email(form.email.data, form.password.data)
            if result and isinstance(result, model.User):
                cache.reset_auth_attempt()
                return signin_user_db(result)
            if result is None and isinstance(form.email.errors, list):
                form.email.errors.append("Email or Password do not match")
            if result is False:
                return flask.redirect(flask.url_for("welcome"))
        if not form.errors:
            form.next_url.data = next_url

    if form and form.errors:
        cache.bump_auth_attempt()

    return flask.render_template(
        "auth/auth.html",
        title="Sign in",
        html_class="auth",
        next_url=next_url,
        form=form,
        form_type="signin" if config.CONFIG_DB.has_email_authentication else "",
        **urls_for_oauth(next_url),
    )


###############################################################################
# Sign up stuff
###############################################################################
class SignUpForm(flask_wtf.FlaskForm):
    """Form for new user registration."""

    email = wtforms.StringField(
        "Email",
        [wtforms.validators.DataRequired(), wtforms.validators.Email()],
        filters=[util.email_filter],
    )
    recaptcha = flask_wtf.RecaptchaField()


@app.route("/signup/", methods=["GET", "POST"])
def signup() -> WerkzeugResponse | str:
    """Handle new user sign-up page rendering and registration submission."""
    next_url = util.get_next_url()
    form = None
    if config.CONFIG_DB.has_email_authentication:
        form = form_with_recaptcha(SignUpForm())
        save_request_params()
        if form.validate_on_submit():
            user_db = model.User.get_by("email", form.email.data)
            if user_db and isinstance(form.email.errors, list):
                form.email.errors.append("This email is already taken.")

            if not form.errors:
                created_user = create_user_db(
                    None,
                    util.create_name_from_email(form.email.data),
                    form.email.data,
                    form.email.data,
                )
                created_user.put()
                task.activate_user_notification(created_user)
                cache.bump_auth_attempt()
                return flask.redirect(flask.url_for("welcome"))

    if form and form.errors:
        cache.bump_auth_attempt()

    title = "Sign up" if config.CONFIG_DB.has_email_authentication else "Sign in"
    return flask.render_template(
        "auth/auth.html",
        title=title,
        html_class="auth",
        next_url=next_url,
        form=form,
        **urls_for_oauth(next_url),
    )


###############################################################################
# Sign out stuff
###############################################################################
@app.route("/signout/")
def signout() -> WerkzeugResponse:
    """Sign out the current user and redirect to next parameter or signin."""
    flask_login.logout_user()
    return flask.redirect(util.param("next") or flask.url_for("signin"))


###############################################################################
# Helpers
###############################################################################
def url_for_signin(service_name: str, next_url: str) -> str:
    """Generate sign-in URL for a specific OAuth provider."""
    return flask.url_for(f"signin_{service_name}", next=next_url)


def urls_for_oauth(next_url: str) -> dict[str, str]:
    """Generate dictionary of sign-in URLs for all supported OAuth providers."""
    return {
        "bitbucket_signin_url": url_for_signin("bitbucket", next_url),
        "facebook_signin_url": url_for_signin("facebook", next_url),
        "github_signin_url": url_for_signin("github", next_url),
        "google_signin_url": url_for_signin("google", next_url),
        "gae_signin_url": url_for_signin("gae", next_url),
        "linkedin_signin_url": url_for_signin("linkedin", next_url),
        "microsoft_signin_url": url_for_signin("microsoft", next_url),
        "twitter_signin_url": url_for_signin("twitter", next_url),
    }


def create_oauth_app(service_config: Mapping[str, object], name: str) -> Any:  # noqa: ANN401
    """Register an OAuth provider application instance."""
    service_oauth = OAuth(app)
    return service_oauth.register(name, **service_config)


def decorator_order_guard(f: Callable[..., Any], decorator_name: str) -> None:
    """Verify that auth decorators are placed below app.route decorators."""
    if f in app.view_functions.values():
        msg = (
            f"Do not use {decorator_name} above app.route decorators as it would not be checked. "
            "Instead move the line below the app.route lines."
        )
        raise SyntaxError(msg)


def save_request_params() -> None:
    """Store next redirect URL and remember choice in user session."""
    flask.session["auth-params"] = {
        "next": util.get_next_url(),
        "remember": util.param("remember", bool),
    }


def save_oauth1_request_token(token: str) -> None:
    """Store OAuth 1.0 request token in session."""
    flask.session["oauth_token"] = token


def fetch_oauth1_request_token() -> str | None:
    """Retrieve OAuth 1.0 request token from session."""
    return flask.session.get("oauth_token")


def signin_oauth(oauth_app: Any, scheme: str | None = None) -> WerkzeugResponse:  # noqa: ANN401
    """Initiate OAuth authorization redirect."""
    try:
        flask.session.pop("oauth_token", None)
        save_request_params()
        redirect_uri = flask.url_for(f"{oauth_app.name}_authorized", _external=True, _scheme=scheme)
        if oauth_app.name == "microsoft":
            redirect_uri = redirect_uri.replace("127.0.0.1", "localhost")
        return oauth_app.authorize_redirect(redirect_uri)  # type: ignore[no-any-return]
    except OAuthError:
        flask.flash(
            "Something went wrong with sign in. Please try again.",
            category="danger",
        )
        return flask.redirect(flask.url_for("signin", next=util.get_next_url()))


def form_with_recaptcha[T: flask_wtf.FlaskForm](form: T) -> T:
    """Conditionally attach reCAPTCHA field to form if attempt limit is reached."""
    should_have_recaptcha = cache.get_auth_attempt() >= config.RECAPTCHA_LIMIT
    if not (should_have_recaptcha and config.CONFIG_DB.has_recaptcha) and hasattr(
        form, "recaptcha"
    ):
        delattr(form, "recaptcha")
    return form


###############################################################################
# User related stuff
###############################################################################
def create_user_db(
    auth_id: str | None,
    name: str,
    username: str,
    email: str = "",
    verified: bool = False,  # noqa: FBT001, FBT002
    **props: object,
) -> model.User:
    """Create a new User entity or link an external auth_id to existing user."""
    email_clean = email.lower() if email else ""
    if verified and email_clean:
        user_dbs, _ = model.User.get_dbs(email=email_clean, verified=True, limit=2)
        if len(user_dbs) == 1:
            existing_user: model.User = user_dbs[0]
            if auth_id:
                existing_user.auth_ids.append(auth_id)
            existing_user.put()
            task.new_user_notification(existing_user)
            return existing_user

    if isinstance(username, bytes):
        username = username.decode("utf-8")
    cleaned_username = unidecode.unidecode(username.split("@", maxsplit=1)[0].lower()).strip()
    cleaned_username = re.sub(r"[\W_]+", ".", cleaned_username)
    new_username = cleaned_username
    n = 1
    while not model.User.is_username_available(new_username):
        new_username = f"{cleaned_username}{n}"
        n += 1

    user_db = model.User(
        name=name,
        email=email_clean,
        token=util.uuid(),
        verified=verified,
        username=new_username,
        auth_ids=[auth_id] if auth_id else [],
        **props,
    )
    user_db.put()
    task.new_user_notification(user_db)
    return user_db


@ndb.toplevel
def signin_user_db(user_db: model.User | None) -> WerkzeugResponse:
    """Authenticate and sign in a user datastore entity."""
    if not user_db:
        return flask.redirect(flask.url_for("signin"))
    flask_user_db = FlaskUser(user_db)
    auth_params = flask.session.get(
        "auth-params",
        {
            "next": flask.url_for("welcome"),
            "remember": False,
        },
    )
    flask.session.pop("auth-params", None)
    if flask_login.login_user(flask_user_db, remember=bool(auth_params.get("remember", False))):
        user_db.put_async()
        return flask.redirect(util.get_next_url(str(auth_params.get("next", ""))))
    flask.flash("Sorry, but you could not sign in.", category="danger")
    return flask.redirect(flask.url_for("signin"))


def get_user_db_from_email(email: str, password: str) -> model.User | bool | None:
    """Retrieve user entity by email and verify password hash."""
    user_dbs, _ = model.User.get_dbs(email=email, active=True, limit=2)
    if not user_dbs:
        return None
    if len(user_dbs) > 1:
        flask.flash(
            "We are sorry but it looks like there is a conflict with "
            "your account. Our support team has been informed and we will get "
            "back to you as soon as possible.",
            category="danger",
        )
        task.email_conflict_notification(email)
        return False

    user_db: model.User = user_dbs[0]
    if user_db.password_hash == util.password_hash(user_db, password):
        return user_db
    return None
