# coding: utf-8

from __future__ import absolute_import

import flask

import auth
import config
import model
import util

from main import app

vk_config = dict(
  access_token_url='https://oauth.vk.com/access_token',
  api_base_url='https://api.vk.com/',
  authorize_url='https://oauth.vk.com/authorize',
  client_id=config.CONFIG_DB.vk_app_id,
  client_secret=config.CONFIG_DB.vk_app_secret,
)

vk = auth.create_oauth_app(vk_config, 'vk')


@app.route('/api/auth/callback/vk/')
def vk_authorized():
  id_token = vk.authorized_access_token()
  if id_token is None:
    flask.flash(u'You denied the request to sign in.')
    return flask.redirect(util.get_next_url())

  flask.session['oauth_token'] = (id_token, '')
  me = vk.get(
    '/method/users.get',
    data={
      'access_token': id_token,
      'format': 'json',
    },
  )
  user_db = retrieve_user_from_vk(me.data['response'][0])
  return auth.signin_user_db(user_db)


@app.route('/signin/vk/')
def signin_vk():
  return auth.signin_oauth(vk)


def retrieve_user_from_vk(response):
  auth_id = 'vk_%s' % response['uid']
  user_db = model.User.get_by('auth_ids', auth_id)
  if user_db:
    return user_db

  name = ' '.join((response['first_name'], response['last_name'])).strip()
  return auth.create_user_db(
    auth_id=auth_id,
    name=name,
    username=name,
  )
