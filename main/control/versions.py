# coding: utf-8

import importlib
import pkg_resources


MODULES = [
  'Crypto',
  'aniso8601',
  'authlib',
  'blinker',
  'certifi',
  'chardet',
  'click',
  'cryptography',
  'flask',
  'flask-login|flask_login',
  'flask-restful|flask_restful.__version__',
  'flask-wtf|flask_wtf',
  'itsdangerous',
  'ipaddress',
  'jinja2',
  'marshmallow',
  'requests',
  'requests_toolbelt',
  'simplejson',
  'unidecode',
  'webargs',
  'werkzeug',
  'wtforms',
]


def get_module_version(spec):
  names = spec.split('|', 1)
  try:
    module = importlib.import_module(names[-1])
  except:
    return (names[0], 'ERROR: Cannot import')
  try:
    version = module.__version__
  except:
    version = 'n/a'
  return (names[0], version)


def get_versions(working_set=True):
  versions = [get_module_version(name) for name in MODULES]
  if working_set:
    for pkg in pkg_resources.working_set:
      name, version = str(pkg).split(' ', 1)
      versions.append(('{} *'.format(name), version))
  versions.sort()
  return versions
