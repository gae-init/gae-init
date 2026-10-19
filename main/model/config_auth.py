from google.cloud import ndb

import model
from api import fields


class ConfigAuth:
    bitbucket_key = ndb.TextProperty(verbose_name="Key", default="")
    bitbucket_secret = ndb.TextProperty(verbose_name="Secret", default="")
    facebook_app_id = ndb.TextProperty(verbose_name="App ID", default="")
    facebook_app_secret = ndb.TextProperty(verbose_name="App Secret", default="")
    github_client_id = ndb.TextProperty(verbose_name="Client ID", default="")
    github_client_secret = ndb.TextProperty(verbose_name="Client Secret", default="")
    google_client_id = ndb.TextProperty(verbose_name="Client ID", default="")
    google_client_secret = ndb.TextProperty(verbose_name="Client Secret", default="")
    linkedin_api_key = ndb.TextProperty(verbose_name="API Key", default="")
    linkedin_secret_key = ndb.TextProperty(verbose_name="Secret Key", default="")
    microsoft_client_id = ndb.TextProperty(verbose_name="Client ID", default="")
    microsoft_client_secret = ndb.TextProperty(verbose_name="Client Secret", default="")
    twitter_consumer_key = ndb.TextProperty(verbose_name="Consumer Key", default="")
    twitter_consumer_secret = ndb.TextProperty(verbose_name="Consumer Secret", default="")

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
    def has_linkedin(self):
        return bool(self.linkedin_api_key and self.linkedin_secret_key)

    @property
    def has_microsoft(self):
        return bool(self.microsoft_client_id and self.microsoft_client_secret)

    @property
    def has_twitter(self):
        return bool(self.twitter_consumer_key and self.twitter_consumer_secret)

    FIELDS = {
        "bitbucket_key": fields.String,
        "bitbucket_secret": fields.String,
        "facebook_app_id": fields.String,
        "facebook_app_secret": fields.String,
        "github_client_id": fields.String,
        "github_client_secret": fields.String,
        "google_client_id": fields.String,
        "google_client_secret": fields.String,
        "linkedin_api_key": fields.String,
        "linkedin_secret_key": fields.String,
        "microsoft_client_id": fields.String,
        "microsoft_client_secret": fields.String,
        "twitter_consumer_key": fields.String,
        "twitter_consumer_secret": fields.String,
    }

    FIELDS.update(model.Base.FIELDS)
