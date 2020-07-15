# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app


def twitch_compliance_fix(session):
  # https://discuss.dev.twitch.tv/t/requiring-oauth-for-helix-twitch-api-endpoints/23916
  def fix_protected_request(url, headers, data):
    headers["Client-ID"] = config.CONFIG_DB.twitch_client_id
    return url, headers, data

  session.register_compliance_hook('protected_request', fix_protected_request)


twitch_config = dict(
  access_token_method='POST',
  access_token_url='https://id.twitch.tv/oauth2/token',
  api_base_url='https://api.twitch.tv/helix/',
  authorize_url='https://id.twitch.tv/oauth2/authorize',
  client_id=config.CONFIG_DB.twitch_client_id,
  client_secret=config.CONFIG_DB.twitch_client_secret,
  client_kwargs={
    'scope': 'user:read:email',
    'token_endpoint_auth_method': 'client_secret_post',
		'Client-ID': config.CONFIG_DB.twitch_client_id,
  },
  compliance_fix=twitch_compliance_fix,

)

twitch = auth.create_oauth_app(twitch_config, 'twitch')


@app.route('/api/auth/callback/twitch/')
def twitch_authorized():
  id_token = twitch.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
  me = twitch.get('users')
  user_db = retrieve_user_from_twitch(me.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/twitch/')
def signin_twitch():
  return auth.signin_oauth(twitch)


def retrieve_user_from_twitch(response):
  respo = response['data'][0]
  auth_id = 'twitch_%s' % respo['id']
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db

  name = respo['display_name']
  username = respo['login']
  email = respo['email']
  return auth.create_user_db(
    auth_id=auth_id,
    name=name,
    username=username or email or name,
    email=email,
    verified=bool(email),
  )
