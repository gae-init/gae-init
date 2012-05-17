try:
  # This part is surrounded in try/except because the this config.py file is
  # also used in the build.py script which is used to compile/minify the client
  # side files (*.less, *.coffee, *.js) and is not aware of the GAE
  import model
  config_db = model.Config.get_master_db()
  BRAND_NAME = config_db.brand_name
  ANALYTICS_ID = config_db.analytics_id
  FACEBOOK_APP_ID = config_db.facebook_app_id
  FACEBOOK_APP_SECRET = config_db.facebook_app_secret
  TWITTER_CONSUMER_KEY = config_db.twitter_consumer_key
  TWITTER_CONSUMER_SECRET = config_db.twitter_consumer_secret
  SECRET_KEY = config_db.flask_secret_key
except:
  BRAND_NAME = 'GAE Init'
  ANALYTICS_ID = ''
  FACEBOOK_APP_ID = ''
  FACEBOOK_APP_SECRET = ''
  TWITTER_CONSUMER_KEY = ''
  TWITTER_CONSUMER_SECRET = ''
  SECRET_KEY = 'not safe'

import os
CURRENT_VERSION_ID = os.environ.get('CURRENT_VERSION_ID', None)
if os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine'):
  DEVELOPMENT = False
else:
  DEVELOPMENT = True

PRODUCTION = not DEVELOPMENT
DEBUG = DEVELOPMENT

DEFAULT_DB_LIMIT = 64

################################################################################
# CLient modules, also used by the build.py script.
################################################################################
STYLES = [
    'src/less/style.less',
  ]

SCRIPTS_MODULES = [
    'libs',
    'site',
  ]

SCRIPTS = {
  'libs': [
    'lib/jquery.js',
    'lib/bootstrap/js/bootstrap-alert.js',
    'lib/bootstrap/js/bootstrap-button.js',
  ],
  'site': [
    'src/coffee/common/util.coffee',
    'src/coffee/common/service.coffee',
    'src/coffee/common/common.coffee',

    'src/coffee/site/app.coffee',
    'src/coffee/site/profile.coffee',
    'src/coffee/site/admin.coffee',
  ],
}
