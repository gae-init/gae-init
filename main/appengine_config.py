# coding: utf-8
import os

from google.appengine.ext import vendor

if not os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
  import sys
  path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'libdev')
  sys.path.insert(0, path)

  if os.name == 'nt':
    import sys

    os.name = None
    sys.platform = ''

import pkg_resources

vendor.add('lib')
pkg_resources.working_set.add_entry('lib')
