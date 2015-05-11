# coding: utf-8

from uuid import uuid4
import hashlib
import re
import unicodedata
import urllib

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import ndb
import flask

import config


###############################################################################
# Request Parameters
###############################################################################
def param(name, cast=None):
  value = None
  if flask.request.json:
    return flask.request.json.get(name, None)

  if value is None:
    value = flask.request.args.get(name, None)
  if value is None and flask.request.form:
    value = flask.request.form.get(name, None)

  if cast and value is not None:
    if cast is bool:
      return value.lower() in ['true', 'yes', 'y', '1', '']
    if cast is list:
      return value.split(',') if len(value) > 0 else []
    if cast is ndb.Key:
      return ndb.Key(urlsafe=value)
    return cast(value)
  return value


def get_next_url(next_url=''):
  next_url = next_url or param('next') or param('next_url')
  do_not_redirect_urls = [flask.url_for(u) for u in [
      'signin', 'signup', 'user_forgot', 'user_reset',
    ]]
  if next_url:
    if any(url in next_url for url in do_not_redirect_urls):
      return flask.url_for('welcome')
    return next_url
  referrer = flask.request.referrer
  if referrer and referrer.startswith(flask.request.host_url):
    return referrer
  return flask.url_for('welcome')


###############################################################################
# Model manipulations
###############################################################################
def get_dbs(
    query, order=None, limit=None, cursor=None, keys_only=None, **filters
  ):
  limit = limit or config.DEFAULT_DB_LIMIT
  cursor = Cursor.from_websafe_string(cursor) if cursor else None
  model_class = ndb.Model._kind_map[query.kind]
  if order:
    for o in order.split(','):
      if o.startswith('-'):
        query = query.order(-model_class._properties[o[1:]])
      else:
        query = query.order(model_class._properties[o])

  for prop in filters:
    if filters.get(prop, None) is None:
      continue
    if isinstance(filters[prop], list):
      for value in filters[prop]:
        query = query.filter(model_class._properties[prop] == value)
    else:
      query = query.filter(model_class._properties[prop] == filters[prop])

  model_dbs, next_cursor, more = query.fetch_page(
      limit, start_cursor=cursor, keys_only=keys_only,
    )
  next_cursor = next_cursor.to_websafe_string() if more else None
  return list(model_dbs), next_cursor


def get_keys(*arg, **kwargs):
  return get_dbs(*arg, keys_only=True, **kwargs)


###############################################################################
# JSON Response Helpers
###############################################################################
def jsonpify(*args, **kwargs):
  if param('callback'):
    content = '%s(%s)' % (
        param('callback'), flask.jsonify(*args, **kwargs).data,
      )
    mimetype = 'application/javascript'
    return flask.current_app.response_class(content, mimetype=mimetype)
  return flask.jsonify(*args, **kwargs)


###############################################################################
# Helpers
###############################################################################
def is_iterable(value):
  return isinstance(value, (tuple, list))


def check_form_fields(*fields):
  fields_data = []
  for field in fields:
    if is_iterable(field):
      fields_data.extend([field.data for field in field])
    else:
      fields_data.append(field.data)
  return all(fields_data)


def generate_next_url(next_cursor, base_url=None, cursor_name='cursor'):
  if not next_cursor:
    return None
  base_url = base_url or flask.request.base_url
  args = flask.request.args.to_dict()
  args[cursor_name] = next_cursor
  return '%s?%s' % (base_url, urllib.urlencode(args))


def uuid():
  return uuid4().hex


_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')


def slugify(text):
  if not isinstance(text, unicode):
    text = unicode(text)
  text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
  text = unicode(_slugify_strip_re.sub('', text).strip().lower())
  return _slugify_hyphenate_re.sub('-', text)


_username_re = re.compile(r'^[a-z0-9]+(?:[\.][a-z0-9]+)*$')


def is_valid_username(username):
  return bool(_username_re.match(username))


def create_name_from_email(email):
  return re.sub(r'_+|-+|\.+|\++', ' ', email.split('@')[0]).title()


def password_hash(user_db, password):
  m = hashlib.sha256()
  m.update(user_db.key.urlsafe())
  m.update(user_db.created.isoformat())
  m.update(m.hexdigest())
  m.update(password.encode('utf-8'))
  m.update(config.CONFIG_DB.salt)
  return m.hexdigest()


def update_query_argument(name, value=None, ignore='cursor', is_list=False):
  ignore = ignore.split(',') if isinstance(ignore, str) else ignore or []
  arguments = {}
  for key, val in flask.request.args.items():
    if key not in ignore and (is_list and value is not None or key != name):
      arguments[key] = val
  if value is not None:
    if is_list:
      values = []
      if name in arguments:
        values = arguments[name].split(',')
        del arguments[name]
      if value in values:
        values.remove(value)
      else:
        values.append(value)
      if values:
        arguments[name] = ','.join(values)
    else:
      arguments[name] = value
  query = '&'.join('%s=%s' % item for item in sorted(arguments.items()))
  return '%s%s' % (flask.request.path, '?%s' % query if query else '')


def parse_tags(tags, separator=None):
  if not is_iterable(tags):
    tags = str(tags.strip()).split(separator or config.TAG_SEPARATOR)
  return filter(None, sorted(list(set(tags))))


###############################################################################
# Lambdas
###############################################################################
strip_filter = lambda x: x.strip() if x else ''
email_filter = lambda x: x.lower().strip() if x else ''
sort_filter = lambda x: sorted(x) if x else []
