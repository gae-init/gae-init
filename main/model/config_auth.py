# coding: utf-8

from __future__ import absolute_import

from google.appengine.ext import ndb

from api import fields
import model


class ConfigAuth(object):
  bitbucket_key = ndb.StringProperty(default='', verbose_name='Key')
  bitbucket_secret = ndb.StringProperty(default='', verbose_name='Secret')
  facebook_app_id = ndb.StringProperty(default='', verbose_name='App ID')
  facebook_app_secret = ndb.StringProperty(default='', verbose_name='App Secret')
  github_client_id = ndb.StringProperty(default='', verbose_name='Client ID')
  github_client_secret = ndb.StringProperty(default='', verbose_name='Client Secret')
  google_client_id = ndb.StringProperty(default='', verbose_name='Client ID')
  google_client_secret = ndb.StringProperty(default='', verbose_name='Client Secret')
  microsoft_client_id = ndb.StringProperty(default='', verbose_name='Client ID')
  microsoft_client_secret = ndb.StringProperty(default='', verbose_name='Client Secret')
  twitter_consumer_key = ndb.StringProperty(default='', verbose_name='Consumer Key')
  twitter_consumer_secret = ndb.StringProperty(default='', verbose_name='Consumer Secret')

  @property
  def has_bitbucket(self):
    return bool(self.bitbucket_key and self.bitbucket_secret)

  @property
  def has_facebook(self):
    return bool(self.facebook_app_id and self.facebook_app_secret)

  @property
  def has_google(self):
    return bool(self.google_client_id and self.google_client_secret)

  @property
  def has_github(self):
    return bool(self.github_client_id and self.github_client_secret)

  @property
  def has_microsoft(self):
    return bool(self.microsoft_client_id and self.microsoft_client_secret)

  @property
  def has_twitter(self):
    return bool(self.twitter_consumer_key and self.twitter_consumer_secret)


  FIELDS = {
    'bitbucket_key': fields.String,
    'bitbucket_secret': fields.String,
    'facebook_app_id': fields.String,
    'facebook_app_secret': fields.String,
    'github_client_id': fields.String,
    'github_client_secret': fields.String,
    'google_client_id': fields.String,
    'google_client_secret': fields.String,
    'microsoft_client_id': fields.String,
    'microsoft_client_secret': fields.String,
    'twitter_consumer_key': fields.String,
    'twitter_consumer_secret': fields.String,
  }

  FIELDS.update(model.Base.FIELDS)
