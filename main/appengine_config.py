# coding: utf-8

import os
import sys

from google.appengine.ext import vendor

vendor.add('venv', 0)

def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = recording.appstats_wsgi_middleware(app)
  return app
