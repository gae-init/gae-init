# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app

linkedin_config = dict(
  access_token_method='POST',
  access_token_url='https://www.linkedin.com/uas/oauth2/accessToken',
  api_base_url='https://api.linkedin.com/v1/',
  authorize_url='https://www.linkedin.com/uas/oauth2/authorization',
  client_id=config.CONFIG_DB.linkedin_api_key,
  client_secret=config.CONFIG_DB.linkedin_secret_key,
  request_token_params={
    'scope': 'r_basicprofile r_emailaddress',
    'state': util.uuid(),
  },
  save_request_token=auth.save_oauth1_request_token,
  fetch_request_token=auth.fetch_oauth1_request_token,
)

linkedin = auth.create_oauth_app(linkedin_config, 'linkedin')


def change_linkedin_query(uri, headers, body):
  headers['x-li-format'] = 'json'
  return uri, headers, body


linkedin.pre_request = change_linkedin_query


@app.route('/api/auth/callback/linkedin/')
def linkedin_authorized():
  id_token = linkedin.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())

  me = linkedin.get('people/~:(id,first-name,last-name,email-address)')
  user_db = retrieve_user_from_linkedin(me.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/linkedin/')
def signin_linkedin():
  return auth.signin_oauth(linkedin)


def retrieve_user_from_linkedin(response):
  auth_id = 'linkedin_%s' % response['id']
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db

  name = response[formatedName]
  email = response.get('emailAddress', '')
  return auth.create_user_db(
    auth_id=auth_id,
    name=name,
    username=email or name,
    email=email,
    verified=bool(email),
  )
