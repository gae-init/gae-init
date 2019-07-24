const gulp = require('gulp-help')(require('gulp'));
const $ = require('gulp-load-plugins')();
const uglify = require('gulp-uglify-es').default;
const config = require('../config');
const paths = require('../paths');
const util = require('../util');

const is_coffee = file => {
  return file.path.indexOf('.coffee') > 0;
};

gulp.task('script', false, () => {
  gulp
    .src(config.script)
    .pipe(
      $.plumber({
        errorHandler: util.onError,
      }),
    )
    .pipe($.if(is_coffee, $.coffee()))
    .pipe($.concat('script.js'))
    .pipe(
      $.babel({
        presets: ['@babel/env'],
      }),
    )
    .pipe(uglify())
    .pipe(
      $.size({
        title: 'Minified scripts',
      }),
    )
    .pipe(gulp.dest(paths.static.min + '/script'));
});

gulp.task('script:dev', false, () => {
  gulp
    .src(config.script)
    .pipe(
      $.plumber({
        errorHandler: util.onError,
      }),
    )
    .pipe($.sourcemaps.init())
    .pipe($.if(is_coffee, $.coffee()))
    .pipe($.concat('script.js'))
    .pipe($.sourcemaps.write())
    .pipe(gulp.dest(paths.static.dev + '/script'));
});
