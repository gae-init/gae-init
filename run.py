#!/usr/bin/env python
# coding: utf-8

from datetime import datetime
from distutils import spawn
import argparse
import json
import os
import platform
import shutil
import socket
import sys
import urllib
import urllib2

__version__ = '6.2.1'


###############################################################################
# Options
###############################################################################
PARSER = argparse.ArgumentParser()
PARSER.add_argument(
  '-d', '--dependencies', dest='install_dependencies', action='store_true',
  help='install virtualenv and python dependencies',
)
PARSER.add_argument(
  '-s', '--start', dest='start', action='store_true',
  help='starts the dev_appserver.py with storage_path pointing to temp',
)
PARSER.add_argument(
  '-o', '--host', dest='host', action='store', default='127.0.0.1',
  help='the host to start the dev_appserver.py',
)
PARSER.add_argument(
  '-p', '--port', dest='port', action='store', default='8080',
  help='the port to start the dev_appserver.py',
)
PARSER.add_argument(
  '--appserver-args', dest='args', nargs=argparse.REMAINDER, default=[],
  help='all following args are passed to dev_appserver.py',
)
PARSER.add_argument(
  '-v', '--version', dest='show_version', action='store_true',
  help='Show gae-init version',
)
ARGS = PARSER.parse_args()


###############################################################################
# Globals
###############################################################################
BAD_ENDINGS = ['pyc', 'pyo', '~']
GAE_PATH = ''
IS_WINDOWS = platform.system() == 'Windows'


###############################################################################
# Directories
###############################################################################
DIR_MAIN = 'main'
DIR_TEMP = 'temp'
DIR_VENV = os.path.join(DIR_TEMP, 'venv')

DIR_LIB = os.path.join(DIR_MAIN, 'lib')
DIR_LIBX = os.path.join(DIR_MAIN, 'libx')
DIR_LIB_DEV = os.path.join(DIR_MAIN, 'libdev')

FILE_REQUIREMENTS = os.path.join(DIR_MAIN, 'requirements.txt')
FILE_DEV_REQUIREMENTS = os.path.join(DIR_MAIN, 'requirements-dev.txt')
FILE_PIP_GUARD = os.path.join(DIR_TEMP, 'pip.guard')
FILE_PIP_DEV_GUARD = os.path.join(DIR_TEMP, 'pip-dev.guard')

FILE_VENV = os.path.join(DIR_VENV, 'Scripts', 'activate.bat') \
  if IS_WINDOWS \
  else os.path.join(DIR_VENV, 'bin', 'activate')

DIR_STORAGE = os.path.join(DIR_TEMP, 'storage')
FILE_UPDATE = os.path.join(DIR_TEMP, 'update.json')


###############################################################################
# Other global variables
###############################################################################
CORE_VERSION_URL = 'https://gae-init.appspot.com/_s/version/'
INTERNET_TEST_URL = 'https://www.google.com'
REQUIREMENTS_URL = 'http://docs.gae-init.appspot.com/requirement/'
TRAVIS = 'TRAVIS' in os.environ

###############################################################################
# Helpers
###############################################################################
def print_out(script, filename=''):
  timestamp = datetime.now().strftime('%H:%M:%S')
  if not filename:
    filename = '-' * 46
    script = script.rjust(12, '-')
  print('[%s] %12s %s' % (timestamp, script, filename))


def make_dirs(directory):
  if not os.path.exists(directory):
    os.makedirs(directory)


def listdir(directory, split_ext=False):
  try:
    if split_ext:
      return [os.path.splitext(dir_)[0] for dir_ in os.listdir(directory)]
    return os.listdir(directory)
  except OSError:
    return []


def site_packages_path():
  if IS_WINDOWS:
    return os.path.join(DIR_VENV, 'Lib', 'site-packages')
  py_version = 'python%s.%s' % sys.version_info[:2]
  return os.path.join(DIR_VENV, 'lib', py_version, 'site-packages')


def create_virtualenv():
  if not os.path.exists(FILE_VENV):
    os.system('virtualenv -p python2 %s' % DIR_VENV)
    os.system('echo %s >> %s' % (
      'set PYTHONPATH=' if IS_WINDOWS else 'unset PYTHONPATH', FILE_VENV
    ))
    pth_file = os.path.join(site_packages_path(), 'gae.pth')
    echo_to = 'echo %s >> {pth}'.format(pth=pth_file)
    os.system(echo_to % find_gae_path())
    os.system(echo_to % os.path.abspath(DIR_LIBX))
  return True


def exec_pip_commands(command):
  script = []
  if create_virtualenv():
    activate_cmd = 'call %s' if IS_WINDOWS else 'source %s'
    activate_cmd %= FILE_VENV
    script.append(activate_cmd)

  script.append('echo %s' % command)
  script.append('%s SKIP_GOOGLEAPICLIENT_COMPAT_CHECK=1' %
                ('set' if IS_WINDOWS else 'export'))
  script.append(command)
  script = '&'.join(script) if IS_WINDOWS else \
      '/bin/bash -c "%s"' % ';'.join(script)
  return os.system(script)


def make_guard(fname, cmd, spec):
  with open(fname, 'w') as guard:
    guard.write('Prevents %s execution if newer than %s' % (cmd, spec))


def guard_is_newer(guard, watched):
  if os.path.exists(guard):
    return os.path.getmtime(guard) > os.path.getmtime(watched)
  return False


def check_if_pip_should_run():
  return not (guard_is_newer(FILE_PIP_GUARD, FILE_REQUIREMENTS) and
              guard_is_newer(FILE_PIP_DEV_GUARD, FILE_DEV_REQUIREMENTS))


def install_py_libs():
  return_code = 0
  if not check_if_pip_should_run() and os.path.exists(DIR_LIB):
    return return_code

  make_guard_flag = True
  if TRAVIS:
    return_code += exec_pip_commands('pip install -v --upgrade -t %s -r %s' % (DIR_LIB_DEV, FILE_DEV_REQUIREMENTS))
    return_code += exec_pip_commands('pip install -v --upgrade -t %s -r %s' % (DIR_LIB, FILE_REQUIREMENTS))
  else:
    return_code = exec_pip_commands('pip install -q -r %s' % FILE_DEV_REQUIREMENTS)
    return_code += exec_pip_commands('pip install --upgrade -t %s -r %s' % (DIR_LIB_DEV, FILE_DEV_REQUIREMENTS))
    return_code += exec_pip_commands('pip install -q -r %s' % FILE_REQUIREMENTS)
    return_code += exec_pip_commands('pip install --upgrade -t %s -r %s' % (DIR_LIB, FILE_REQUIREMENTS))
  if return_code:
    print('ERROR running pip install')
    make_guard_flag = False

  if make_guard_flag:
    make_guard(FILE_PIP_GUARD, 'pip', FILE_REQUIREMENTS)
    make_guard(FILE_PIP_DEV_GUARD, 'pip', FILE_DEV_REQUIREMENTS)
  return return_code


def install_dependencies():
  make_dirs(DIR_TEMP)
  return install_py_libs()


def check_for_update():
  if os.path.exists(FILE_UPDATE):
    mtime = os.path.getmtime(FILE_UPDATE)
    last = datetime.utcfromtimestamp(mtime).strftime('%Y-%m-%d')
    today = datetime.utcnow().strftime('%Y-%m-%d')
    if last == today:
      return
  try:
    with open(FILE_UPDATE, 'a'):
      os.utime(FILE_UPDATE, None)
    request = urllib2.Request(
      CORE_VERSION_URL,
      urllib.urlencode({'version': __version__}),
    )
    response = urllib2.urlopen(request)
    with open(FILE_UPDATE, 'w') as update_json:
      update_json.write(response.read())
  except (urllib2.HTTPError, urllib2.URLError):
    pass


def print_out_update(force_show=False):
  try:
    import pip
    SemVer = pip.util.version.SemanticVersion
  except AttributeError:
    import pip._vendor.distlib.version
    SemVer = pip._vendor.distlib.version.SemanticVersion

  try:
    with open(FILE_UPDATE, 'r') as update_json:
      data = json.load(update_json)
    if SemVer(__version__) < SemVer(data['version']) or force_show:
      print_out('UPDATE')
      print_out(data['version'], 'Latest version of gae-init')
      print_out(__version__, 'Your version is a bit behind')
      print_out('CHANGESET', data['changeset'])
  except (ValueError, KeyError):
    os.remove(FILE_UPDATE)
  except IOError:
    pass


###############################################################################
# Doctor
###############################################################################
def internet_on():
  try:
    urllib2.urlopen(INTERNET_TEST_URL, timeout=2)
    return True
  except (urllib2.URLError, socket.timeout):
    return False


def check_requirement(check_func):
  result, name, help_url_id = check_func()
  if not result:
    print_out('NOT FOUND', name)
    if help_url_id:
      print('Please see %s%s' % (REQUIREMENTS_URL, help_url_id))
    return False
  return True


def find_gae_path():
  global GAE_PATH
  if GAE_PATH:
    return GAE_PATH
  if IS_WINDOWS:
    gae_path = None
    for path in os.environ['PATH'].split(os.pathsep):
      if os.path.isfile(os.path.join(path, 'dev_appserver.py')):
        gae_path = path
  else:
    gae_path = spawn.find_executable('dev_appserver.py')
    if gae_path:
      gae_path = os.path.dirname(os.path.realpath(gae_path))
  if not gae_path:
    return ''
  gcloud_exec = 'gcloud.cmd' if IS_WINDOWS else 'gcloud'
  if not os.path.isfile(os.path.join(gae_path, gcloud_exec)):
    GAE_PATH = gae_path
  else:
    gae_path = os.path.join(gae_path, '..', 'platform', 'google_appengine')
    if os.path.exists(gae_path):
      GAE_PATH = os.path.realpath(gae_path)
  return GAE_PATH


def check_internet():
  return internet_on(), 'Internet', ''


def check_gae():
  return bool(find_gae_path()), 'Google App Engine SDK', '#gae'


def check_git():
  return bool(spawn.find_executable('git')), 'Git', '#git'


def check_nodejs():
  return bool(spawn.find_executable('node')), 'Node.js', '#nodejs'


def check_pip():
  return bool(spawn.find_executable('pip')), 'pip', '#pip'


def check_virtualenv():
  return bool(spawn.find_executable('virtualenv')), 'virtualenv', '#virtualenv'


def doctor_says_ok():
  checkers = [check_gae, check_git, check_nodejs, check_pip, check_virtualenv]
  if False in [check_requirement(check) for check in checkers]:
    sys.exit(1)
  return check_requirement(check_internet)


###############################################################################
# Main
###############################################################################
def run_start():
  make_dirs(DIR_STORAGE)
  port = int(ARGS.port)
  run_command = ' '.join(map(str, [
    'dev_appserver.py',
    DIR_MAIN,
    '--host %s' % ARGS.host,
    '--port %s' % port,
    '--admin_port %s' % (port + 1),
    '--storage_path=%s' % DIR_STORAGE,
    '--skip_sdk_update_check',
  ] + ARGS.args))
  os.system(run_command)


def run():
  return_code = 0
  if len(sys.argv) == 1 or (ARGS.args and not ARGS.start):
    PARSER.print_help()
    sys.exit(1)

  os.chdir(os.path.dirname(os.path.realpath(__file__)))

  if doctor_says_ok():
    return_code |= install_dependencies()
    check_for_update()

  if ARGS.show_version:
    print_out_update(force_show=True)
  else:
    print_out_update()

  if ARGS.start:
    run_start()

  if ARGS.install_dependencies:
    return_code |= install_dependencies()

  sys.exit(return_code)


if __name__ == '__main__':
  run()
