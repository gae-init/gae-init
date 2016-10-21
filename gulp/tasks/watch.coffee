gulp = require('gulp-help') require 'gulp'
$ = do require 'gulp-load-plugins'
paths = require '../paths'

POLL_INTERVAL = 500

gulp.task 'reload', false, ->
  do $.livereload.listen
  gulp.watch([
    "#{paths.static.dev}/**/*.{css,js}"
    "#{paths.main}/**/*.{html,py}"
  ], { interval: POLL_INTERVAL }).on 'change', $.livereload.changed


gulp.task 'ext_watch_rebuild', false, (callback) ->
  $.sequence('clean:dev', 'copy_bower_files', 'ext:dev', 'style:dev') callback


gulp.task 'watch', false, ->
  gulp.watch 'requirements.txt', { interval: POLL_INTERVAL }, ['pip']
  gulp.watch 'package.json', { interval: POLL_INTERVAL }, ['npm']
  gulp.watch 'bower.json', { interval: POLL_INTERVAL }, ['ext_watch_rebuild']
  gulp.watch 'gulp/config.coffee', { interval: POLL_INTERVAL }, ['ext:dev', 'style:dev', 'script:dev']
  gulp.watch paths.static.ext, { interval: POLL_INTERVAL }, ['ext:dev']
  gulp.watch "#{paths.src.script}/**/*.coffee", { interval: POLL_INTERVAL }, ['script:dev']
  gulp.watch "#{paths.src.style}/**/*.less", { interval: POLL_INTERVAL }, ['style:dev']
