# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app

bitbucket_config = dict(
  access_token_method='POST',
  access_token_url='https://bitbucket.org/site/oauth2/access_token',
  api_base_url='https://api.bitbucket.org/2.0/',
  authorize_url='https://bitbucket.org/site/oauth2/authorize',
  client_id=config.CONFIG_DB.bitbucket_key,
  client_secret=config.CONFIG_DB.bitbucket_secret,
  client_kwargs={'scope': 'email'},
)

bitbucket = auth.create_oauth_app(bitbucket_config, 'bitbucket')


@app.route('/api/auth/callback/bitbucket/')
def bitbucket_authorized():
  err = flask.request.args.get('error')
  if err in ['access_denied']:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
  id_token = bitbucket.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
  me = bitbucket.get('user')
  user_db = retrieve_user_from_bitbucket(me.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/bitbucket/')
def signin_bitbucket():
  return auth.signin_oauth(bitbucket)


def retrieve_user_from_bitbucket(response):
  auth_id = 'bitbucket_%s' % response['username']
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db
  emails_response = bitbucket.get('user/emails')
  emails = emails_response.json().get('values', [])
  email = ''.join([e['email'] for e in emails if e['is_primary']][0:1])
  return auth.create_user_db(
    auth_id=auth_id,
    name=response['display_name'],
    username=response['username'],
    email=email,
    verified=bool(email),
  )
