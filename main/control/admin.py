# coding: utf-8

from datetime import datetime
from datetime import timedelta
import flask
import flask_wtf
import wtforms

import auth
import config
import model
import task
import util

from main import app


###############################################################################
# Admin Stuff
###############################################################################
@app.route('/admin/')
@auth.admin_required
def admin():
  localhost = None
  if config.DEVELOPMENT and ':' in flask.request.host:
    try:
      parts = flask.request.host.split(':')
      port = int(parts[1]) + 1
      localhost = 'http://%s:%s/' % (parts[0], port)
    except:
      pass

  return flask.render_template(
    'admin/admin.html',
    title='Admin',
    html_class='admin',
    localhost=localhost,
  )


###############################################################################
# Config Stuff
###############################################################################
class ConfigUpdateForm(flask_wtf.FlaskForm):
  analytics_id = wtforms.StringField(model.Config.analytics_id._verbose_name, filters=[util.strip_filter])
  announcement_html = wtforms.TextAreaField(model.Config.announcement_html._verbose_name, filters=[util.strip_filter])
  announcement_type = wtforms.SelectField(model.Config.announcement_type._verbose_name, choices=[(t, t.title()) for t in model.Config.announcement_type._choices])
  anonymous_recaptcha = wtforms.BooleanField(model.Config.anonymous_recaptcha._verbose_name)
  brand_name = wtforms.StringField(model.Config.brand_name._verbose_name, [wtforms.validators.required()], filters=[util.strip_filter])
  check_unique_email = wtforms.BooleanField(model.Config.check_unique_email._verbose_name)
  email_authentication = wtforms.BooleanField(model.Config.email_authentication._verbose_name)
  feedback_email = wtforms.StringField(model.Config.feedback_email._verbose_name, [wtforms.validators.optional(), wtforms.validators.email()], filters=[util.email_filter])
  flask_secret_key = wtforms.StringField(model.Config.flask_secret_key._verbose_name, [wtforms.validators.optional()], filters=[util.strip_filter])
  letsencrypt_challenge = wtforms.StringField(model.Config.letsencrypt_challenge._verbose_name, filters=[util.strip_filter])
  letsencrypt_response = wtforms.StringField(model.Config.letsencrypt_response._verbose_name, filters=[util.strip_filter])
  notify_on_new_user = wtforms.BooleanField(model.Config.notify_on_new_user._verbose_name)
  recaptcha_private_key = wtforms.StringField(model.Config.recaptcha_private_key._verbose_name, filters=[util.strip_filter])
  recaptcha_public_key = wtforms.StringField(model.Config.recaptcha_public_key._verbose_name, filters=[util.strip_filter])
  salt = wtforms.StringField(model.Config.salt._verbose_name, [wtforms.validators.optional()], filters=[util.strip_filter])
  trusted_hosts = wtforms.StringField(model.Config.trusted_hosts._verbose_name, [wtforms.validators.optional()], description='Comma separated: 127.0.0.1, example.com, etc')
  verify_email = wtforms.BooleanField(model.Config.verify_email._verbose_name)


@app.route('/admin/config/', methods=['GET', 'POST'])
@auth.admin_required
def admin_config():
  config_db = model.Config.get_master_db()
  form = ConfigUpdateForm(obj=config_db)
  if form.validate_on_submit():
    if form.trusted_hosts.data:
      form.trusted_hosts.data = set(
        [e.strip() for e in form.trusted_hosts.data.split(',')])
    else:
      form.trusted_hosts.data = []
    form.populate_obj(config_db)
    if not config_db.flask_secret_key:
      config_db.flask_secret_key = util.uuid()
    if not config_db.salt:
      config_db.salt = util.uuid()
    config_db.put()
    reload(config)
    app.config.update(CONFIG_DB=config_db)
    return flask.redirect(flask.url_for('admin'))
  form.trusted_hosts.data = ', '.join(config_db.trusted_hosts)

  return flask.render_template(
    'admin/admin_config.html',
    title='App Config',
    html_class='admin-config',
    form=form,
    api_url=flask.url_for('api.admin.config'),
  )


###############################################################################
# Auth Stuff
###############################################################################
class AuthUpdateForm(flask_wtf.FlaskForm):
  azure_ad_client_id = wtforms.StringField(model.Config.azure_ad_client_id._verbose_name, filters=[util.strip_filter])
  azure_ad_client_secret = wtforms.StringField(model.Config.azure_ad_client_secret._verbose_name, filters=[util.strip_filter])
  bitbucket_key = wtforms.StringField(model.Config.bitbucket_key._verbose_name, filters=[util.strip_filter])
  bitbucket_secret = wtforms.StringField(model.Config.bitbucket_secret._verbose_name, filters=[util.strip_filter])
  dropbox_app_key = wtforms.StringField(model.Config.dropbox_app_key._verbose_name, filters=[util.strip_filter])
  dropbox_app_secret = wtforms.StringField(model.Config.dropbox_app_secret._verbose_name, filters=[util.strip_filter])
  facebook_app_id = wtforms.StringField(model.Config.facebook_app_id._verbose_name, filters=[util.strip_filter])
  facebook_app_secret = wtforms.StringField(model.Config.facebook_app_secret._verbose_name, filters=[util.strip_filter])
  github_client_id = wtforms.StringField(model.Config.github_client_id._verbose_name, filters=[util.strip_filter])
  github_client_secret = wtforms.StringField(model.Config.github_client_secret._verbose_name, filters=[util.strip_filter])
  google_client_id = wtforms.StringField(model.Config.google_client_id._verbose_name, filters=[util.strip_filter])
  google_client_secret = wtforms.StringField(model.Config.google_client_secret._verbose_name, filters=[util.strip_filter])
  instagram_client_id = wtforms.StringField(model.Config.instagram_client_id._verbose_name, filters=[util.strip_filter])
  instagram_client_secret = wtforms.StringField(model.Config.instagram_client_secret._verbose_name, filters=[util.strip_filter])
  linkedin_api_key = wtforms.StringField(model.Config.linkedin_api_key._verbose_name, filters=[util.strip_filter])
  linkedin_secret_key = wtforms.StringField(model.Config.linkedin_secret_key._verbose_name, filters=[util.strip_filter])
  mailru_app_id = wtforms.StringField(model.Config.mailru_app_id._verbose_name, filters=[util.strip_filter])
  mailru_app_secret = wtforms.StringField(model.Config.mailru_app_secret._verbose_name, filters=[util.strip_filter])
  microsoft_client_id = wtforms.StringField(model.Config.microsoft_client_id._verbose_name, filters=[util.strip_filter])
  microsoft_client_secret = wtforms.StringField(model.Config.microsoft_client_secret._verbose_name, filters=[util.strip_filter])
  reddit_client_id = wtforms.StringField(model.Config.reddit_client_id._verbose_name, filters=[util.strip_filter])
  reddit_client_secret = wtforms.StringField(model.Config.reddit_client_secret._verbose_name, filters=[util.strip_filter])
  twitter_consumer_key = wtforms.StringField(model.Config.twitter_consumer_key._verbose_name, filters=[util.strip_filter])
  twitter_consumer_secret = wtforms.StringField(model.Config.twitter_consumer_secret._verbose_name, filters=[util.strip_filter])
  vk_app_id = wtforms.StringField(model.Config.vk_app_id._verbose_name, filters=[util.strip_filter])
  vk_app_secret = wtforms.StringField(model.Config.vk_app_secret._verbose_name, filters=[util.strip_filter])
  yahoo_consumer_key = wtforms.StringField(model.Config.yahoo_consumer_key._verbose_name, filters=[util.strip_filter])
  yahoo_consumer_secret = wtforms.StringField(model.Config.yahoo_consumer_secret._verbose_name, filters=[util.strip_filter])


@app.route('/admin/auth/', methods=['GET', 'POST'])
@auth.admin_required
def admin_auth():
  config_db = model.Config.get_master_db()
  form = AuthUpdateForm(obj=config_db)
  if form.validate_on_submit():
    form.populate_obj(config_db)
    config_db.put()
    reload(config)
    app.config.update(CONFIG_DB=config_db)
    return flask.redirect(flask.url_for('admin'))

  return flask.render_template(
    'admin/admin_auth.html',
    title='Auth Config',
    html_class='admin-auth',
    form=form,
    api_url=flask.url_for('api.admin.config'),
  )


###############################################################################
# Stats Stuff
###############################################################################
@app.route('/admin/stats/<string:duration>/')
@app.route('/admin/stats/')
def admin_stats(duration='day'):
  if duration not in ['day', 'week', 'month', 'year']:
    flask.abort(404)

  stats_dbs, stats_cursor = model.Stats.get_dbs(
    duration=duration,
    order=util.param('order') or '-timestamp',
    limit=util.param('limit', int) or 60 if duration == 'day' else -1,
  )

  return flask.render_template(
    'admin/stats.html',
    html_class='admin-stats admin-stats-%s' % duration,
    title='Stats - %s' % duration.title(),
    stats_dbs=stats_dbs,
    duration=duration,
  )


@app.route('/admin/stats/calc/<int:year>-<int:month>-<int:day>/')
@app.route('/admin/stats/calc/<int:year>-<int:month>/')
@app.route('/admin/stats/calc/<string:when>/')
@app.route('/admin/stats/calc/<int:year>/')
@app.route('/admin/stats/calc/')
@auth.cron_required
def admin_stats_calc(when='', year=0, month=0, day=0):
  if not year:
    utc_now = datetime.utcnow()
    year = utc_now.year
    month = utc_now.month
    day = utc_now.day

  duration = 'day'

  if when == 'yesterday':
    timestamp = datetime.utcnow() + timedelta(-1)
  else:
    if day == 0:
      duration = 'month'
      day = 1
    if month == 0:
      duration = 'year'
      month = 1
    timestamp = datetime(year, month, day)

  start, finish = util.date_limits(timestamp, duration)

  total = 0
  while start < finish:
    task.task_calculate_stats(start)
    start += timedelta(1)
    total += 1

  if util.param('redirect', bool):
    flask.flash('Started %d task(s) for the %s: %s' % (
      total, duration, timestamp.strftime('%d %B %Y')
    ), category='success')
    return flask.redirect(flask.url_for('admin_stats'))
  return '%d tasks in %s - %s' % (total, duration, timestamp.strftime('%d %B %Y'))
