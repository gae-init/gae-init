# coding: utf-8

import flask
from flask_webpack import Webpack
import config
import util

webpack = Webpack()

class GaeRequest(flask.Request):
  trusted_hosts = config.TRUSTED_HOSTS

app = flask.Flask(__name__)
app.config.from_object(config)

params = {
  'DEBUG': config.DEVELOPMENT,
  'WEBPACK_MANIFEST_PATH': './static/manifest.json'
}
app.config.update(params)
if config.PRODUCTION:
  app.config.update({'WEBPACK_ASSETS_URL': '/p/dist/'})

webpack.init_app(app)
app.request_class = GaeRequest if config.TRUSTED_HOSTS else flask.Request

app.jinja_env.line_statement_prefix = '#'
app.jinja_env.line_comment_prefix = '##'
app.jinja_env.globals.update(
  check_form_fields=util.check_form_fields,
  is_iterable=util.is_iterable,
  slugify=util.slugify,
  update_query_argument=util.update_query_argument,
)

import auth
import control
import model
import task

from api import helpers

api_v1 = helpers.Api(app, prefix='/api/v1')

import api.v1

if config.DEVELOPMENT:
  from werkzeug import debug
  try:
    app.wsgi_app = debug.DebuggedApplication(
      app.wsgi_app, evalex=True, pin_security=False,
    )
  except TypeError:
    app.wsgi_app = debug.DebuggedApplication(app.wsgi_app, evalex=True)
  app.testing = False
