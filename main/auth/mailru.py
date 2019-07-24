# coding: utf-8

from __future__ import absolute_import

import hashlib

import flask

import auth
import config
import model
import util

from main import app

mailru_config = dict(
  access_token_url='https://connect.mail.ru/oauth/token',
  api_base_url='https://www.appsmail.ru/',
  authorize_url='https://connect.mail.ru/oauth/authorize',
  client_id=config.CONFIG_DB.mailru_app_id,
  client_secret=config.CONFIG_DB.mailru_app_secret,
)

mailru = auth.create_oauth_app(mailru_config, 'mailru')


def mailru_sig(data):
  param_list = sorted(['%s=%s' % (item, data[item]) for item in data])
  return hashlib.md5(''.join(param_list) + mailru.consumer_secret).hexdigest()


@app.route('/api/auth/callback/mailru/')
def mailru_authorized():
  id_token = mailru.authorize_access_token()
  if id_token is None:
    flask.flash(u'You denied the request to sign in.')
    return flask.redirect(util.get_next_url())

  flask.session['oauth_token'] = (id_token, '')
  data = {
    'method': 'users.getInfo',
    'app_id': mailru.consumer_key,
    'session_key': id_token,
    'secure': '1',
  }
  data['sig'] = mailru_sig(data)
  me = mailru.get('/platform/api', data=data)
  user_db = retrieve_user_from_mailru(me.data[0])
  return auth.signin_user_db(user_db)


@app.route('/signin/mailru/')
def signin_mailru():
  return auth.signin_oauth(mailru)


def retrieve_user_from_mailru(response):
  auth_id = 'mailru_%s' % response['uid']
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db
  name = u' '.join([
    response.get('first_name', u''),
    response.get('last_name', u'')
  ]).strip()
  email = response.get('email', '')
  return auth.create_user_db(
    auth_id=auth_id,
    name=name or email,
    username=email or name,
    email=email,
    verified=bool(email),
  )
