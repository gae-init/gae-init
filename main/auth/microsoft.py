# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app

microsoft_config = dict(
  access_token_method='POST',
  access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
  api_base_url='https://graph.microsoft.com/v1.0/users/',
  authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
  client_id=config.CONFIG_DB.microsoft_client_id,
  client_secret=config.CONFIG_DB.microsoft_client_secret,
  client_kwargs={'scope': 'https://graph.microsoft.com/user.read'},
)

microsoft = auth.create_oauth_app(microsoft_config, 'microsoft')


@app.route('/api/auth/callback/microsoft/')
def microsoft_authorized():
  id_token = microsoft.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
  me = microsoft.get('me')
  user_db = retrieve_user_from_microsoft(me.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/microsoft/')
def signin_microsoft():
  return auth.signin_oauth(microsoft)


def retrieve_user_from_microsoft(response):
  auth_id = 'microsoft_%s' % response['id']
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db
  email = response['userPrincipalName']
  name = response.get('displayName', '')
  return auth.create_user_db(
    auth_id=auth_id,
    name=name,
    username=name or email,
    email=email,
    verified=bool(email),
  )
