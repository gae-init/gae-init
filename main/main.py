# coding: utf-8

# Set up logging directly to google cloud
# per https://cloud.google.com/logging/docs/setup/python
import logging
import google.cloud.logging
client = google.cloud.logging.Client()  # Instantiates a client
client.setup_logging(log_level=logging.DEBUG)  # Connects the logger to the root logging handler

import flask

import config
import util


class GaeRequest(flask.Request):
  trusted_hosts = config.TRUSTED_HOSTS


app = flask.Flask(__name__)
app.config.from_object(config)
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
