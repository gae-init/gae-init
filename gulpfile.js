const gulp = require('gulp-help')(require('gulp'));
// eslint-disable-next-line
const requireDir = require('require-dir')('./gulp/tasks');
const $ = require('gulp-load-plugins')();

gulp.task(
  'default',
  'Start the local server, watch for changes and reload browser automatically. For available options refer to "run" task.',
  $.sequence('run', ['watch']),
);
