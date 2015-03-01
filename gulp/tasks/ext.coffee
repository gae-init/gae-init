gulp = require('gulp-help') require 'gulp'
$ = do require 'gulp-load-plugins'
config = require '../config'
paths = require '../paths'
utils = require '../utils'


gulp.task 'ext', false, ->
  gulp.src config.ext
  .pipe $.plumber(errorHandler: utils.onError)
  .pipe $.concat 'ext.js'
  .pipe do $.uglify
  .pipe $.size {title: 'Minified ext libs'}
  .pipe gulp.dest "#{paths.static.min}/script"


gulp.task 'ext:dev', false, ->
  gulp.src config.ext
  .pipe $.plumber(errorHandler: utils.onError)
  .pipe do $.sourcemaps.init
  .pipe $.concat 'ext.js'
  .pipe do $.sourcemaps.write
  .pipe gulp.dest "#{paths.static.dev}/script"
