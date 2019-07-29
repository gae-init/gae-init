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
  return user_db or auth.create_user_db(
    auth_id=auth_id,
    name=response['name'] or response['login'],
    username=response['login'],
    email=response.get('email', ''),
    verified=bool(response.get('email', '')),
  )


#localhost:3000 vs 127.0.0.1:8080 issue
# http://127.0.0.1:8080/api/auth/callback/github/

# Need to compare what gets returned by 
# flask.url_for(
#      '%s_authorized' % oauth_app.name, _external=True, _scheme=scheme
#    )

# With the URL on the auth config page
#http://localhost:3000/api/auth/callback/github/?error=redirect_uri_mismatch&error_description=The+redirect_uri+MUST+match+the+registered+callback+URL+for+this+application.&error_uri=https%3A%2F%2Fdeveloper.github.com%2Fapps%2Fmanaging-oauth-apps%2Ftroubleshooting-authorization-request-errors%2F%23redirect-uri-mismatch&state=r1awNd3oT3XgWMLIX1ZheZHenIEvJZ