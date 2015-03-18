# coding: utf-8

from __future__ import absolute_import

from google.appengine.ext import ndb

from api import fields
import model


class ConfigAuth(object):
  bitbucket_key = ndb.StringProperty(default='', verbose_name='Key')
  bitbucket_secret = ndb.StringProperty(default='', verbose_name='Secret')
  dropbox_app_key = ndb.StringProperty(default='', verbose_name='App Key')
  dropbox_app_secret = ndb.StringProperty(default='', verbose_name='App Secret')
  facebook_app_id = ndb.StringProperty(default='', verbose_name='App ID')
  facebook_app_secret = ndb.StringProperty(default='', verbose_name='App Secret')
  github_client_id = ndb.StringProperty(default='', verbose_name='Client ID')
  github_client_secret = ndb.StringProperty(default='', verbose_name='Client Secret')
  google_client_id = ndb.StringProperty(default='', verbose_name='Client ID')
  google_client_secret = ndb.StringProperty(default='', verbose_name='Client Secret')
  instagram_client_id = ndb.StringProperty(default='', verbose_name='Client ID')
  instagram_client_secret = ndb.StringProperty(default='', verbose_name='Client Secret')
  linkedin_api_key = ndb.StringProperty(default='', verbose_name='API Key')
  linkedin_secret_key = ndb.StringProperty(default='', verbose_name='Secret Key')
  microsoft_client_id = ndb.StringProperty(default='', verbose_name='Client ID')
  microsoft_client_secret = ndb.StringProperty(default='', verbose_name='Client Secret')
  twitter_consumer_key = ndb.StringProperty(default='', verbose_name='Consumer Key')
  twitter_consumer_secret = ndb.StringProperty(default='', verbose_name='Consumer Secret')
  vk_app_id = ndb.StringProperty(default='', verbose_name='App ID')
  vk_app_secret = ndb.StringProperty(default='', verbose_name='App Secret')
  yahoo_consumer_key = ndb.StringProperty(default='', verbose_name='Consumer Key')
  yahoo_consumer_secret = ndb.StringProperty(default='', verbose_name='Consumer Secret')

  @property
  def has_bitbucket(self):
    return bool(self.bitbucket_key and self.bitbucket_secret)

  @property
  def has_dropbox(self):
    return bool(self.dropbox_app_key and self.dropbox_app_secret)

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
  def has_instagram(self):
    return bool(self.instagram_client_id and self.instagram_client_secret)

  @property
  def has_linkedin(self):
    return bool(self.linkedin_api_key and self.linkedin_secret_key)

  @property
  def has_microsoft(self):
    return bool(self.microsoft_client_id and self.microsoft_client_secret)

  @property
  def has_twitter(self):
    return bool(self.twitter_consumer_key and self.twitter_consumer_secret)

  @property
  def has_vk(self):
    return bool(self.vk_app_id and self.vk_app_secret)

  @property
  def has_yahoo(self):
    return bool(self.yahoo_consumer_key and self.yahoo_consumer_secret)

  FIELDS = {
      'bitbucket_key': fields.String,
      'bitbucket_secret': fields.String,
      'dropbox_app_key': fields.String,
      'dropbox_app_secret': fields.String,
      'facebook_app_id': fields.String,
      'facebook_app_secret': fields.String,
      'github_client_id': fields.String,
      'github_client_secret': fields.String,
      'google_client_id': fields.String,
      'google_client_secret': fields.String,
      'instagram_client_id': fields.String,
      'instagram_client_secret': fields.String,
      'linkedin_api_key': fields.String,
      'linkedin_secret_key': fields.String,
      'microsoft_client_id': fields.String,
      'microsoft_client_secret': fields.String,
      'twitter_consumer_key': fields.String,
      'twitter_consumer_secret': fields.String,
      'vk_app_id': fields.String,
      'vk_app_secret': fields.String,
      'yahoo_consumer_key': fields.String,
      'yahoo_consumer_secret': fields.String,
    }

  FIELDS.update(model.Base.FIELDS)
