# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app

facebook_config = dict(
  access_token_url='https://graph.facebook.com/v4.0/oauth/access_token',
  api_base_url='https://graph.facebook.com/v4.0/',
  authorize_url='https://www.facebook.com/v4.0/dialog/oauth',
  client_id=config.CONFIG_DB.facebook_app_id,
  client_secret=config.CONFIG_DB.facebook_app_secret,
  request_token_params={'scope': 'email'},
)

facebook = auth.create_oauth_app(facebook_config, 'facebook')


@app.route('/api/auth/callback/facebook/')
def facebook_authorized():
  id_token = facebook.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())

  me = facebook.get('/me?fields=id,name,email')
  user_db = retrieve_user_from_facebook(me.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/facebook/')
def signin_facebook():
  return auth.signin_oauth(facebook)


def retrieve_user_from_facebook(response):
  auth_id = 'facebook_%s' % response['id']
  user_db = model.User.get_by('auth_ids', auth_id)
  name = response['name']
  return user_db or auth.create_user_db(
    auth_id=auth_id,
    name=name,
    username=name,
    email=response.get('email', ''),
    verified=bool(response.get('email', '')),
  )
