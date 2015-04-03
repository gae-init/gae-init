fs = require 'fs'
gulp = require('gulp-help') require 'gulp'

main_bower_files = require 'main-bower-files'
del = require 'del'
exec = require('child_process').exec
merge = require 'merge-stream'
minimist = require 'minimist'

$ = do require 'gulp-load-plugins'


dir_bower_components = 'bower_components'
dir_main = 'main'
dir_node_modules = 'node_modules'

dir_lib = "#{dir_main}/lib"
dir_libx = "#{dir_main}/libx"
dir_temp = 'temp'
dir_venv = "#{dir_temp}/venv"

file_lib = "#{dir_lib}.zip"

dir_static = "#{dir_main}/static"
dir_src = "#{dir_static}/src"
dir_script = "#{dir_src}/script"
dir_style = "#{dir_src}/style"
dir_build = "#{dir_static}/build"
dir_ext = "#{dir_build}/ext"
dir_min = "#{dir_static}/min"
dir_storage = "#{dir_temp}/storage"


paths =
  ext: [
      "#{dir_ext}/jquery/dist/jquery.js"
      "#{dir_ext}/moment/moment.js"
      "#{dir_ext}/nprogress/nprogress.js"
      "#{dir_ext}/bootstrap/js/alert.js"
      "#{dir_ext}/bootstrap/js/button.js"
      "#{dir_ext}/bootstrap/js/transition.js"
      "#{dir_ext}/bootstrap/js/collapse.js"
      "#{dir_ext}/bootstrap/js/dropdown.js"
      "#{dir_ext}/bootstrap/js/tooltip.js"
    ]
  clean: [
      dir_ext
      dir_min
      './**/*.pyc'
      './**/*.pyo'
      './**/*.~'
    ]
  clean_all: [
      dir_min
      dir_bower_components
      dir_node_modules
      "#{dir_temp}/pip.guard"
    ]
  clean_py: [
      dir_lib
      dir_venv
    ]
  style: [
      "#{dir_style}/style.less"
    ]
  script: [
      "#{dir_build}/script/common/api.js"
      "#{dir_build}/script/common/util.js"
      "#{dir_build}/script/site/admin.js"
      "#{dir_build}/script/site/auth.js"
      "#{dir_build}/script/site/user.js"
      "#{dir_build}/script/site/app.js"
    ]
  watch: [
      "#{dir_static}/**/*.css"
      "#{dir_static}/**/*.js"
      "#{dir_main}/**/*.html"
      "#{dir_main}/**/*.py"
    ]


onError = (err) ->
  do $.util.beep
  console.log err
  this.emit 'end'


gulp.task 'script', false, ->
  gulp.src "#{dir_script}/**/*.coffee"
    .pipe $.plumber(errorHandler: onError)
    .pipe do $.sourcemaps.init
    .pipe $.coffee()
    .pipe do $.sourcemaps.write
    .pipe gulp.dest "#{dir_build}/script"


gulp.task 'style', false, ->
  gulp.src paths.style
    .pipe $.plumber(errorHandler: onError)
    .pipe do $.sourcemaps.init
    .pipe do $.less
    .pipe do $.sourcemaps.write
    .pipe $.autoprefixer {map: true}
    .pipe gulp.dest "#{dir_build}/style"


gulp.task 'inject', false, ->
  gulp.src("#{dir_main}/templates/bit/script.html")
    .pipe $.plumber()
    .pipe $.inject(gulp.src(paths.script),
      name: 'script'
      addRootSlash: false
      ignorePath: 'main/static'
      addPrefix: '/p'
    )
    .pipe $.inject(gulp.src(paths.ext),
      name: 'ext'
      addRootSlash: false
      ignorePath: 'main/static'
      addPrefix: '/p'
    )
    .pipe gulp.dest "#{dir_main}/templates/bit"



gulp.task 'clean',
'Clean the project from temp files, Python compiled files
and minified styles and scripts.', ->
  del paths.clean
  del paths.clean_py


gulp.task 'init',
'Complete cleaning the project: cleans all the
Pip requirements, temp files, Node & Bower related tools and libraries.', ->
  del paths.clean
  del paths.clean_all
  del paths.clean_py


gulp.task 'bower', false, ->
  if /^win/.test process.platform
    start_map = [{match: /bower.json$/, cmd: 'node_modules\\.bin\\bower install'}]
  else
    start_map = [{match: /bower.json$/, cmd: 'node_modules/.bin/bower install'}]
  gulp.src('bower.json')
    .pipe $.plumber()
    .pipe $.start start_map


gulp.task 'npm', false, ->
  gulp.src('package.json')
    .pipe $.plumber()
    .pipe do $.start


gulp.task 'ext_install', false, ['bower'], ->
  gulp.src do main_bower_files, base: dir_bower_components
    .pipe gulp.dest dir_ext


gulp.task 'build',
  "Compiles styles & scripts files into minified version
  and pack python dependencies into #{file_lib}.",
  $.sequence 'clean', 'install_dependencies', ['script', 'style', 'zip'], 'inject'


gulp.task 'rebuild',
  'Re-build the project: complete cleaning and install & build all requirements again.',
  $.sequence 'init', 'build'


gulp.task 'install_dependencies', false, $.sequence 'npm', 'pip', 'ext_install'


gulp.task 'reload', false, ->
  do $.livereload.listen
  gulp.watch(paths.watch).on 'change', $.livereload.changed


gulp.task 'ext_watch_rebuild', false, (callback) ->
  $.sequence('ext_install', 'style') callback


gulp.task 'watch', false, ->
  gulp.watch 'requirements.txt', ['pip']
  gulp.watch 'package.json', ['npm']
  gulp.watch 'bower.json', ['ext_watch_rebuild']
  gulp.watch "#{dir_script}/**/*.coffee", ['script']
  gulp.watch "#{dir_style}/**/*.less", ['style']


gulp.task 'min', false, ->
  ext = gulp.src paths.ext
    .pipe $.plumber(errorHandler: onError)
    .pipe $.concat 'ext.js'
    .pipe do $.uglify
    .pipe $.size {title: 'Minified ext libs'}
    .pipe gulp.dest "#{dir_min}/script"

  script = gulp.src paths.script
    .pipe $.plumber(errorHandler: onError)
    .pipe $.concat 'script.js'
    .pipe do $.uglify
    .pipe $.size {title: 'Minified script libs'}
    .pipe gulp.dest "#{dir_min}/script"

  style = gulp.src paths.style
    .pipe $.plumber(errorHandler: onError)
    .pipe do $.less
    .pipe $.autoprefixer {cascade: false}
    .pipe do $.minifyCss
    .pipe $.size {title: 'Minified styles'}
    .pipe gulp.dest "#{dir_min}/style"

  merge(ext, script, style)


########################## Tasks for App Engine ################################

gulp.task 'pip', false, ->
  gulp.src('run.py').pipe $.start [{match: /run.py$/, cmd: 'python run.py -d'}]


gulp.task 'flush', 'Clears the datastore, blobstore, etc', ->
  del dir_storage


gulp.task 'zip', false, ->
  fs.exists file_lib, (exists) ->
    if not exists
      fs.exists dir_lib, (exists) ->
        if exists
          gulp.src "#{dir_lib}/**"
              .pipe $.plumber()
              .pipe $.zip 'lib.zip'
              .pipe gulp.dest dir_main



gulp.task 'deploy', 'Deploying your project on Google App Engine', ->
  $.sequence('build', 'min') ->
    gulp.src('run.py').pipe $.start [
        {match: /run.py$/, cmd: 'appcfg.py update main --skip_sdk_update_check --application=topless-pro --version=gae'}
      ]


gulp.task 'run',
'Start the dev_appserver.py. Available options:\n
-o HOST - the host to start the dev_appserver.py\n
-p PORT - the port to start the dev_appserver.py\n
-a="..." - all following args are passed to dev_appserver.py\n', ->
  $.sequence('install_dependencies', ['script', 'style'], 'inject') ->
    argv = process.argv.slice 2

    known_options =
      default:
        p: ''
        o: ''
        a: ''

    options = minimist argv, known_options

    options_str = ''
    for k of known_options.default
      if options[k]
        if k == 'a'
          options_str += " --appserver-args \"#{options[k]}\""
        else
          options_str += " -#{k} #{options[k]}"

    gulp.src('run.py').pipe $.start [{match: /run.py$/, cmd: 'python run.py -s'}]


gulp.task 'default',
  'Start the dev_appserver.py, watching changes and LiveReload.
Available options - please see "run" task.',
  $.sequence 'run', ['watch', 'reload']
