#!/usr/bin/env python
# coding: utf-8


import os
import sys
import getpass
try:
  import readline
except ImportError:
  readline = None
import atexit
import urllib2
from code import interact
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('-l', dest='shell', action='store_true',
    help='Start a new interactive python shell',
 )
parser.add_argument('-r', dest='rshell', action='store_true',
    help='Start a new interactive remote python shell',
 )
args = parser.parse_args()


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.join(CURRENT_DIR, "main")
PROJECT_LIBS = os.path.join(PROJECT_DIR, "lib")
STORAGE_DIR = os.path.join(CURRENT_DIR, 'temp', 'storage')


def setup_env():
  try:
    from google.appengine.api import apiproxy_stub_map
    import yaml
  except ImportError, e:
    paths = []
    for path in os.environ.get('PATH', '').replace(';', ':').split(':'):
      path = path.rstrip(os.sep)
      if path.endswith('google_appengine'):
        paths.append(path)
    if os.name == 'nt':
      paths.append(
          os.path.join(os.environ['PROGRAMFILES'], '\Google\google_appengine')
        )

    SDK_PATH = None
    for dir_path in paths:
      dir_path = os.path.realpath(dir_path)
      if os.path.exists(dir_path):
        SDK_PATH = dir_path
        break
    if SDK_PATH is None:
      sys.stderr.write(
          'The GAE SDK could not be found! Please visit http://goo.gl/g1memX'
          ' for installation instructions.\n'
        )
      sys.exit(1)

    EXTRA_PATHS = [SDK_PATH]
    gae_libs = os.path.join(SDK_PATH, 'lib')
    for pkg_dir in os.listdir(gae_libs):
      path = os.path.join(gae_libs, pkg_dir)

      # skip all django packages
      if pkg_dir.startswith('django'):
        continue

      # use latest webapp2, webob, yaml
      if pkg_dir.startswith('webapp2'):
        if pkg_dir != 'webapp2-2.5.2':
          continue
      if pkg_dir.startswith('webob'):
        if pkg_dir != 'webob-1.2.3':
          continue
      if pkg_dir.startswith('yaml'):
        if pkg_dir == 'yaml':
          continue

      # 'lib/<pkg>/<pkg>/' or 'lib/<pkg>/lib/<pkg>/' or 'lib/<pkg-x.x.x>/<pkg>
      detect_pkg = (
          os.path.join(path, pkg_dir),
          os.path.join(path, 'lib', pkg_dir),
          os.path.join(path, pkg_dir.split('-')[0]),
        )
      for path in detect_pkg:
        if os.path.isdir(path):
          EXTRA_PATHS.append(os.path.dirname(path))
          break
      sys.path = EXTRA_PATHS + sys.path + [PROJECT_DIR] + [PROJECT_LIBS]

    if sys.modules.has_key('google'):
      del sys.modules['google']


def init_stubs(appid, storage_path):
  from google.appengine.datastore import datastore_sqlite_stub
  from google.appengine.datastore import datastore_v4_stub
  from google.appengine.api.files import file_service_stub
  from google.appengine.api.memcache import memcache_stub
  from google.appengine.api.logservice import logservice_stub
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.api.search import simple_search_stub

  datastore_path = os.path.join(storage_path, 'datastore.db')
  logs_path = os.path.join(storage_path, 'logs.db')
  search_index_path = os.path.join(storage_path, 'search_indexes')
  blobstore_path = os.path.join(storage_path, 'blobs')
  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
  datastore_stub = datastore_sqlite_stub.DatastoreSqliteStub(
    appid,
    datastore_path,
    root_path=PROJECT_DIR
  )
  apiproxy_stub_map.apiproxy.ReplaceStub(
    'datastore_v3', datastore_stub
  )
  apiproxy_stub_map.apiproxy.RegisterStub(
    'datastore_v4',
    datastore_v4_stub.DatastoreV4Stub(appid)
  )
  apiproxy_stub_map.apiproxy.RegisterStub(
    'file',
    file_service_stub.FileServiceStub(blobstore_path)
  )
  apiproxy_stub_map.apiproxy.RegisterStub(
    'memcache',
    memcache_stub.MemcacheServiceStub()
  )
  apiproxy_stub_map.apiproxy.RegisterStub(
    'logservice',
    logservice_stub.LogServiceStub(logs_path=logs_path)
  )
  apiproxy_stub_map.apiproxy.RegisterStub(
    'search',
    simple_search_stub.SearchServiceStub(index_file=search_index_path)
  )


def get_appconfig(is_dev=True):
  try:
    from google.appengine.tools import dev_appserver
    appconfig, unused, cache = dev_appserver.LoadAppConfig(PROJECT_DIR, {})

    if is_dev:
      appconfig.application = 'dev~%s' % appconfig.application

    if not os.environ.get('APPLICATION_ID'):
      os.environ['APPLICATION_ID'] = appconfig.application
    if not os.environ.get('CURRENT_VERSION_ID'):
      os.environ['CURRENT_VERSION_ID'] = appconfig.version + ".1"
  except ImportError:
    appconfig = None
    print "Error"
  return appconfig


def get_appid(is_dev=True):
  from google.appengine.api import apiproxy_stub_map
  have_appserver = bool(apiproxy_stub_map.apiproxy.GetStub('datastore_v3'))
  if have_appserver:
    return os.environ.get('APPLICATION_ID')
  app_id = get_appconfig(is_dev).application
  return app_id


def run_interact(appid, banner, namespace, storage_path):
  sys.ps1 = '%s> ' % appid
  if readline is not None:
    readline.parse_and_bind('tab: complete')
    HISTORY_PATH = os.path.join(storage_path, '.history')
    atexit.register(lambda: readline.write_history_file(HISTORY_PATH))
    if os.path.exists(HISTORY_PATH):
      readline.read_history_file(HISTORY_PATH)
  interact(banner, local=namespace)


def run_ipython(appid, banner, namespace):
  import IPython
  from IPython.config.loader import Config
  cfg = Config()
  prompt_config = cfg.PromptManager
  prompt_config.in_template = '%s> ' % appid
  prompt_config.out_template = '%s>: ' % appid
  IPython.embed(config=cfg, user_ns=namespace, banner2=banner)


def run_shell(appid, banner, storage_path=STORAGE_DIR):
  namespace = {}
  try:
    run_ipython(appid, banner, namespace)
  except ImportError:
    run_interact(appid, banner, namespace, storage_path)


def shell(storage_path=STORAGE_DIR):
  setup_env()
  appid = get_appid()
  init_stubs(appid, storage_path)
  banner = '=== Welcome to gae-init shell ==='
  run_shell(appid, banner, storage_path)


def auth_func():
  return raw_input('Username:'), getpass.getpass('Password:')


def rshell(storage_path=STORAGE_DIR):
  setup_env()
  appid = get_appid(False)
  host = "%s.appspot.com" % appid
  path = '/_ah/remote_api'

  from google.appengine.ext.remote_api import remote_api_stub
  try:
    remote_api_stub.ConfigureRemoteApi(None, path, auth_func,
      host, secure=True, save_cookies=True)
  except urllib2.HTTPError:
    print "Unable to connect to %s%s" % (host, path)
    exit()
  remote_api_stub.MaybeInvokeAuthentication()

  banner = ("=== Welcome to gae-init remote shell ====\n"
            "---------- Please be careful ------------")
  run_shell(host, banner, storage_path)


if __name__ == "__main__":
  if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

  if args.shell:
    shell()

  if args.rshell:
    rshell()
