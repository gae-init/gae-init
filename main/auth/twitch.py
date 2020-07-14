# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app

twitch_config = dict(
  access_token_method='POST',
  access_token_url='https://id.twitch.tv/oauth2/token',
  api_base_url='https://api.twitch.tv/helix/',
  authorize_url='https://id.twitch.tv/oauth2/authorize',
  client_id=config.CONFIG_DB.twitch_client_id,
  client_secret=config.CONFIG_DB.twitch_client_secret,
  request_token_params={
    'scope': 'user:read:email;user:read:stream_key',
    'token_endpoint_auth_method': 'client_secret_post',
  },
)

twitch = auth.create_oauth_app(twitch_config, 'twitch')


@app.route('/api/auth/callback/twitch/')
def twitch_authorized():
  id_token = twitch.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())

  me = twitch.get('user')  # Need to change this line
  user_db = retrieve_user_from_twitch(me.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/twitch/')
def signin_twitch():
  return auth.signin_oauth(twitch)


def retrieve_user_from_twitch(response):
  auth_id = 'twitch_%s' % response['id']
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db

  name = response['display_name']
  username = response.get('display_name', '')
  email = response.get('email', '')
  return auth.create_user_db(
    auth_id=auth_id,
    name=name,
    username=username or email or name,
    email=email,
    verified=bool(email),
  )
