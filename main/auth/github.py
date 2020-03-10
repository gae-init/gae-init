# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app

github_config = dict(
  access_token_method='POST',
  access_token_url='https://github.com/login/oauth/access_token',
  api_base_url='https://api.github.com/',
  authorize_url='https://github.com/login/oauth/authorize',
  client_id=config.CONFIG_DB.github_client_id,
  client_secret=config.CONFIG_DB.github_client_secret,
  request_token_params={'scope': 'user:email'},
)

github = auth.create_oauth_app(github_config, 'github')


@app.route('/api/auth/callback/github/')
def github_authorized():
  id_token = github.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
  me = github.get('user')
  user_db = retrieve_user_from_github(me.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/github/')
def signin_github():
  return auth.signin_oauth(github)


def retrieve_user_from_github(response):
  auth_id = 'github_%s' % str(response['id'])
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db
  email = response.get('email', '')
  return auth.create_user_db(
    auth_id=auth_id,
    name=response['name'] or response['login'],
    username=response['login'],
    email=email,
    verified=bool(email),
  )
