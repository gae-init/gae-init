# coding: utf-8

from datetime import datetime
import logging

from flask.ext import restful
from werkzeug import exceptions
import flask

import util


class Api(restful.Api):
  def unauthorized(self, response):
    flask.abort(401)

  def handle_error(self, e):
    return handle_error(e)


def handle_error(e):
  logging.exception(e)
  try:
    e.code
  except AttributeError:
    e.code = 500
    e.name = e.description = 'Internal Server Error'
  return util.jsonpify({
      'status': 'error',
      'error_code': e.code,
      'error_name': util.slugify(e.name),
      'error_message': e.name,
      'error_class': e.__class__.__name__,
      'description': e.description,
    }), e.code


def make_response(data, marshal_table, next_cursor=None):
  if util.is_iterable(data):
    response = {
        'status': 'success',
        'count': len(data),
        'now': datetime.utcnow().isoformat(),
        'result': map(lambda l: restful.marshal(l, marshal_table), data),
      }
    if next_cursor:
      response['next_cursor'] = next_cursor
      response['next_url'] = util.generate_next_url(next_cursor)
    return util.jsonpify(response)
  return util.jsonpify({
      'status': 'success',
      'now': datetime.utcnow().isoformat(),
      'result': restful.marshal(data, marshal_table),
    })


def make_not_found_exception(description):
  exception = exceptions.NotFound()
  exception.description = description
  raise exception
