# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app


twitter_config = dict(
  access_token_url='https://api.twitter.com/oauth/access_token',
  api_base_url='https://api.twitter.com/1.1/',
  authorize_url='https://api.twitter.com/oauth/authenticate',
  client_id=config.CONFIG_DB.twitter_consumer_key,
  client_secret=config.CONFIG_DB.twitter_consumer_secret,
  request_token_url='https://api.twitter.com/oauth/request_token',
  signature_method='HMAC-SHA1',
  save_request_token=auth.save_oauth1_request_token,
  fetch_request_token=auth.fetch_oauth1_request_token,
)

twitter = auth.create_oauth_app(twitter_config, 'twitter')



@app.route('/api/auth/callback/twitter/')
def twitter_authorized():
  id_token = twitter.authorize_access_token()
  if id_token is None:
    flask.flash('You denied the request to sign in.')
    return flask.redirect(util.get_next_url())
    
  response = twitter.get('account/verify_credentials.json')
  user_db = retrieve_user_from_twitter(response.json())
  return auth.signin_user_db(user_db)


@app.route('/signin/twitter/')
def signin_twitter():
  return auth.signin_oauth(twitter)


def retrieve_user_from_twitter(response):
  auth_id = 'twitter_%s' % response['id_str']
  user_db = model.User.get_by('auth_ids', auth_id)
  return user_db or auth.create_user_db(
    auth_id=auth_id,
    name=response['name'] or response['screen_name'],
    username=response['screen_name'],
  )
