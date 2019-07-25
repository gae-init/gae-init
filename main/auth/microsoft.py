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
  access_token_url='https://login.live.com/oauth20_token.srf',
  api_base_url='https://apis.live.net/v5.0/',
  authorize_url='https://login.live.com/oauth20_authorize.srf',
  client_id=config.CONFIG_DB.microsoft_client_id,
  client_secret=config.CONFIG_DB.microsoft_client_secret,
  request_token_params={'scope': 'wl.emails'},
)

microsoft = auth.create_oauth_app(microsoft_config, 'microsoft')


@app.route('/api/auth/callback/microsoft/')
def microsoft_authorized():
  id_token = microsoft.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
  flask.session['oauth_token'] = (id_token, '')
  me = microsoft.get('me')
  if me.data.get('error', {}):
    return 'Unknown error: error:%s error_description:%s' % (
      me['error']['code'],
      me['error']['message'],
    )
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
  email = response['emails']['preferred'] or response['emails']['account']
  return auth.create_user_db(
    auth_id=auth_id,
    name=response.get('name', ''),
    username=email,
    email=email,
    verified=bool(email),
  )
