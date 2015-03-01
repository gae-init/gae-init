gulp = require('gulp-help') require 'gulp'
$ = do require 'gulp-load-plugins'
config = require '../config'
paths = require '../paths'
utils = require '../utils'


gulp.task 'script', false, ->
  gulp.src config.script
  .pipe $.plumber(errorHandler: utils.onError)
  .pipe $.coffee()
  .pipe $.concat 'script.js'
  .pipe do $.uglify
  .pipe $.size {title: 'Minified scripts'}
  .pipe gulp.dest "#{paths.static.min}/script"


gulp.task 'script:dev', false, ->
  gulp.src config.script
  .pipe $.plumber(errorHandler: utils.onError)
  .pipe do $.sourcemaps.init
  .pipe $.coffee()
  .pipe $.concat 'script.js'
  .pipe do $.sourcemaps.write
  .pipe gulp.dest "#{paths.static.dev}/script"
