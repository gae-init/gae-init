# coding: utf-8

import os
import sys

from google.appengine.ext import vendor


if os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine'):
  sys.path.insert(0, 'lib.zip')
else:
  if os.name == 'nt':
    os.name = None
    sys.platform = ''

  vendor.add('venv', 0)

sys.path.insert(0, 'libx')


def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = recording.appstats_wsgi_middleware(app)
  return app
