const fs = require('fs');
const gulp = require('gulp-help')(require('gulp'));
const yarn = require('gulp-yarn');
const main_bower_files = require('main-bower-files');
const $ = require('gulp-load-plugins')();
const paths = require('../paths');

gulp.task('yarn', false, () => {
  gulp
    .src(['./package.json', './yarn.lock'])
    .pipe($.plumber())
    .pipe(yarn());
});

gulp.task('bower', false, () => {
  let cmd = 'node_modules/.bin/bower install';
  if (/^win/.test(process.platform)) {
    cmd = cmd.replace(/\//g, '\\');
  }
  const start_map = [
    {
      cmd: cmd,
      match: /bower.json$/,
    },
  ];
  gulp
    .src('bower.json')
    .pipe($.plumber())
    .pipe($.start(start_map));
});

gulp.task('copy_bower_files', false, ['bower'], () => {
  gulp
    .src(main_bower_files(), {
      base: paths.dep.bower_components,
    })
    .pipe(gulp.dest(paths.static.ext));
});

gulp.task('pip', false, () => {
  gulp.src('run.py').pipe(
    $.start([
      {
        cmd: 'python run.py -d',
        match: /run.py$/,
      },
    ]),
  );
});

gulp.task('zip', false, () => {
  fs.exists(paths.py.lib_file, exists => {
    if (!exists) {
      fs.exists(paths.py.lib, exists_ => {
        if (exists_) {
          gulp
            .src(paths.py.lib + '/**')
            .pipe($.plumber())
            .pipe($.zip('lib.zip'))
            .pipe(gulp.dest(paths.main));
        }
      });
    }
  });
});

gulp.task('init', false, $.sequence('pip', 'copy_bower_files'));
