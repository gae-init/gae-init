# coding: utf-8

from __future__ import absolute_import

import flask
import json

import auth
import config
import model
import util

from main import app


linkedin_config = dict(
  access_token_method='POST',
  access_token_url='https://www.linkedin.com/uas/oauth2/accessToken',
  api_base_url='https://api.linkedin.com/v2/',
  authorize_url='https://www.linkedin.com/uas/oauth2/authorization',
  client_id=config.CONFIG_DB.linkedin_api_key,
  client_secret=config.CONFIG_DB.linkedin_secret_key,
  client_kwargs={
    'scope': 'r_liteprofile r_emailaddress',
    'state': util.uuid(),
    'token_endpoint_auth_method': 'client_secret_post',
  },
)


linkedin = auth.create_oauth_app(linkedin_config, 'linkedin')


@app.route('/api/auth/callback/linkedin/')
def linkedin_authorized():
  err = flask.request.args.get('error')
  if err in ['user_cancelled_login', 'user_cancelled_authorize']:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
  id_token = linkedin.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
  me = linkedin.get('me?projection=(id,firstName,lastName)')
  user_db = retrieve_user_from_linkedin(me.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/linkedin/')
def signin_linkedin():
  return auth.signin_oauth(linkedin)


def dict_gets(dct, k, default=None, sep='|'):
  # lookup by walking path in object
  keys = k.split(sep)
  data = dct
  try:
    for key in keys:
      data = data[key]
  except:
    data = default
  return data


def get_localized_value(data, key):
  locale = '{}_{}'.format(
    dict_gets(data, k='{}|preferredLocale|language'.format(key), default='en'),
    dict_gets(data, k='{}|preferredLocale|country'.format(key), default='US'),
  )
  return dict_gets(data, k='{}|localized|{}'.format(key, locale), default='')


def get_email_address(data):
  email = ''
  emails = dict_gets(data, k='elements', default=[])
  if isinstance(emails, list) and len(emails):
    for e in emails:
      email = dict_gets(e, k='handle~|emailAddress', default='')
      if email:
        break
  elif isinstance(emails, dict):
    # according to the API documentation this could be returned
    email = dict_gets(emails, k='handle~|emailAddress', default='')
  return email


def retrieve_user_from_linkedin(response):
  auth_id = 'linkedin_%s' % response['id']
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db
  name = ' '.join([
    get_localized_value(response, 'firstName'),
    get_localized_value(response, 'lastName'),
  ]).strip()
  email_response = linkedin.get('emailAddress?q=members&projection=(elements*(handle~))')
  email = get_email_address(email_response.json())
  return auth.create_user_db(
    auth_id=auth_id,
    name=name,
    username=email or name,
    email=email,
    verified=bool(email),
  )
