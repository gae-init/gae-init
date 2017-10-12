gulp = require('gulp-help') require 'gulp'
$ = require('gulp-load-plugins')()
config = require '../config'
paths = require '../paths'
util = require '../util'


is_coffee = (file) ->
  return file.path.indexOf('.coffee') > 0


is_ts = (file) ->
  return file.path.indexOf('.ts') > 0


ts_project = $.typescript.createProject paths.tsconfig_file


gulp.task 'script', false, ->
  gulp.src config.script
  .pipe $.plumber errorHandler: util.onError
  .pipe $.if is_coffee, $.coffee()
  .pipe $.if is_ts, ts_project()
  .pipe $.concat 'script.js'
  .pipe $.uglify()
  .pipe $.size {title: 'Minified scripts'}
  .pipe gulp.dest "#{paths.static.min}/script"


gulp.task 'script:dev', false, ->
  gulp.src config.script
  .pipe $.plumber errorHandler: util.onError
  .pipe $.sourcemaps.init()
  .pipe $.if is_coffee, $.coffee()
  .pipe $.if is_ts, ts_project()
  .pipe $.concat 'script.js'
  .pipe $.sourcemaps.write()
  .pipe gulp.dest "#{paths.static.dev}/script"
