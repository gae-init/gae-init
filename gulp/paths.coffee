paths =
  main: 'main'

  dep: {}
  py: {}
  static: {}
  src: {}
  temp: {}

paths.temp.root = 'temp'
paths.temp.storage = "#{paths.temp.root}/storage"
paths.temp.venv = "#{paths.temp.root}/venv"
paths.dep.bower_components = 'bower_components'
paths.dep.node_modules = 'node_modules'
paths.dep.py = "#{paths.temp.root}/venv"
paths.dep.py_guard = "#{paths.temp.root}/pip.guard"
paths.py.lib = "#{paths.main}/lib"
paths.py.lib_file = "#{paths.py.lib}.zip"
paths.static.root = "#{paths.main}/static"
paths.src.root = "#{paths.static.root}/src"


module.exports = paths
