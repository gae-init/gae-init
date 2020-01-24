const gulp = require('gulp');

const browserSync = require('browser-sync');
const del = require('del');
const fs = require('fs');
const main_bower_files = require('main-bower-files');
const uglify = require('gulp-uglify-es').default;
const usage = require('gulp-help-doc');
const yargs = require('yargs-parser');
const yarn = require('gulp-yarn');

const config = require('./gulp/config');
const paths = require('./gulp/paths');
const util = require('./gulp/util');

gulp.task('help', () => {
  return usage(gulp);
});

// eslint-disable-next-line
const $ = require('gulp-load-plugins')();

/**
 * Start the local server, watch for changes and reload browser automatically.
 * For available options refer to "run" task.
 * @task {default}
 * @order {1}
 */
gulp.task('default', $.sequence('run', ['watch']));

/*** Build ***/

/**
 * Build project to prepare it for a deployment. Minify CSS & JS files and pack
 * Python dependencies into #{paths.py.lib_file}.
 * @task {build}
 * @arg {dryrun} Run all preparations but do not actually deploy
 * @arg {[other]} Other arguments are passed through to gcloud app deploy
 ***/
gulp.task(
  'build',
  $.sequence('clean:min', 'init', 'ext', ['script', 'style', 'zip']),
);

/*
  Re-build project from scratch. Equivalent to "reset" and "build" tasks.
  @task {rebuild}
  */
gulp.task('rebuild', $.sequence('reset', 'build'));

/**
  Deploy project to Google App Engine.
  @task {deploy}
  **/
gulp.task('deploy', ['build'], () => {
  let dryrun;
  let k_iterator;
  let options_str;
  const options = yargs(process.argv, {
    configuration: {
      'boolean-negation': false,
      'camel-case-expansion': false,
    },
  });
  delete options._;
  options_str = '';
  dryrun = '';
  for (k_iterator in options) {
    if (k_iterator === 'dryrun') {
      dryrun = 'echo DRYRUN - would run: ';
    } else {
      if (options[k_iterator] === true) {
        options[k_iterator] = '';
      }
      options_str += ` ${k_iterator.length > 1 ? '-' : ''}-${k_iterator} ${
        options[k_iterator]
      }`;
    }
  }
  return gulp.src('run.py').pipe(
    $.start([
      {
        cmd: `${dryrun}gcloud app deploy main/*.yaml${options_str}`,
        match: /run.py$/,
      },
    ]),
  );
});

/**
  Start the local server. Available options:
  @arg {-o HOST} the host to start the dev_appserver.py
  @arg {-p PORT} the port to start the dev_appserver.py
  @arg {-a="..."} all following args are passed to dev_appserver.py
  @task {run}
  **/
gulp.task('run', () => {
  return $.sequence('init', ['ext:dev', 'script:dev', 'style:dev'])(() => {
    let k_iterator;
    let options_str;
    const argv = process.argv.slice(2);
    const known_options = {
      default: {
        // eslint-disable-next-line
        a: '',
        // eslint-disable-next-line
        o: '',
        // eslint-disable-next-line
        p: '',
      },
    };
    const options = yargs(argv);
    options_str = '-s';
    for (k_iterator in known_options.default) {
      if (options[k_iterator]) {
        if (k_iterator === 'a') {
          options_str += ` --appserver-args "${options[k_iterator]}"`;
        } else {
          options_str += ` -${k_iterator} ${options[k_iterator]}`;
        }
      }
    }
    if (options.p) {
      config.port = options.p;
    }
    if (options.o) {
      config.host = options.o;
    }
    gulp.start('browser-sync');
    return gulp.src('run.py').pipe(
      $.start([
        {
          cmd: `python run.py ${options_str}`,
          match: /run.py$/,
        },
      ]),
    );
  });
});

/*** Clean ***/

/**
Clean project from temporary files, generated CSS & JS and compiled Python
files.
@task {clean}
**/
gulp.task('clean', () => {
  del('./**/*.pyc');
  del('./**/*.pyo');
  return del('./**/*.~');
});

gulp.task('clean:dev', false, () => {
  del(paths.static.ext);
  return del(paths.static.dev);
});

gulp.task('clean:min', false, () => {
  del(paths.static.ext);
  return del(paths.static.min);
});

gulp.task('clean:venv', false, () => {
  del(paths.py.lib);
  del(paths.py.lib_file);
  del(paths.dep.py);
  return del(paths.dep.py_guard);
});

/**
Complete reset of project. Run "yarn install" after this procedure.
@task {reset}
**/
gulp.task('reset', ['clean', 'clean:dev', 'clean:min', 'clean:venv'], () => {
  del(paths.dep.bower_components);
  return del(paths.dep.node_modules);
});

/**
Clear local datastore, blobstore, etc.
@task {flush}
**/
gulp.task('flush', () => {
  return del(paths.temp.storage);
});

/*** Dep ***/

gulp.task('yarn', () => {
  return gulp
    .src(['./package.json', './yarn.lock'])
    .pipe($.plumber())
    .pipe(yarn());
});

gulp.task('bower', () => {
  let cmd;
  cmd = 'node_modules/.bin/bower install';
  if (/^win/.test(process.platform)) {
    cmd = cmd.replace(/\//g, '\\');
  }
  const start_map = [
    {
      cmd: cmd,
      match: /bower.json$/,
    },
  ];
  return gulp
    .src('bower.json')
    .pipe($.plumber())
    .pipe($.start(start_map));
});

gulp.task('copy_bower_files', ['bower'], () => {
  return gulp
    .src(main_bower_files(), {
      base: paths.dep.bower_components,
    })
    .pipe(gulp.dest(paths.static.ext));
});

gulp.task('pip', () => {
  return gulp.src('run.py').pipe(
    $.start([
      {
        cmd: 'python run.py -d',
        match: /run.py$/,
      },
    ]),
  );
});

gulp.task('zip', () => {
  return fs.exists(paths.py.lib_file, exists => {
    if (!exists) {
      return fs.exists(paths.py.lib, exists2 => {
        if (exists2) {
          return gulp
            .src(`${paths.py.lib}/**`)
            .pipe($.plumber())
            .pipe($.zip('lib.zip'))
            .pipe(gulp.dest(paths.main));
        }
      });
    }
  });
});

gulp.task('init', $.sequence('pip', 'copy_bower_files'));

/*** Ext ***/

gulp.task('ext', () => {
  return gulp
    .src(config.ext)
    .pipe(
      $.plumber({
        errorHandler: util.onError,
      }),
    )
    .pipe($.concat('ext.js'))
    .pipe(uglify())
    .pipe(
      $.size({
        title: 'Minified ext libs',
      }),
    )
    .pipe(gulp.dest(`${paths.static.min}/script`));
});

gulp.task('ext:dev', () => {
  return gulp
    .src(config.ext)
    .pipe(
      $.plumber({
        errorHandler: util.onError,
      }),
    )
    .pipe($.sourcemaps.init())
    .pipe($.concat('ext.js'))
    .pipe($.sourcemaps.write())
    .pipe(gulp.dest(`${paths.static.dev}/script`));
});

/*** Script ***/

gulp.task('script', () => {
  return gulp
    .src(config.script)
    .pipe(
      $.plumber({
        errorHandler: util.onError,
      }),
    )
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
    .pipe(gulp.dest(`${paths.static.min}/script`));
});

gulp.task('script:dev', () => {
  return gulp
    .src(config.script)
    .pipe(
      $.plumber({
        errorHandler: util.onError,
      }),
    )
    .pipe($.sourcemaps.init())
    .pipe($.concat('script.js'))
    .pipe($.sourcemaps.write())
    .pipe(gulp.dest(`${paths.static.dev}/script`));
});

/*** Style ***/
gulp.task('style', () => {
  return gulp
    .src(config.style)
    .pipe(
      $.plumber({
        errorHandler: util.onError,
      }),
    )
    .pipe($.less())
    .pipe(
      $.cssnano({
        discardComments: {
          removeAll: true,
        },
        zindex: false,
      }),
    )
    .pipe(
      $.size({
        title: 'Minified styles',
      }),
    )
    .pipe(gulp.dest(`${paths.static.min}/style`));
});

gulp.task('style:dev', () => {
  return gulp
    .src(config.style)
    .pipe(
      $.plumber({
        errorHandler: util.onError,
      }),
    )
    .pipe($.sourcemaps.init())
    .pipe($.less())
    .pipe(
      $.autoprefixer({
        map: true,
      }),
    )
    .pipe($.sourcemaps.write())
    .pipe(gulp.dest(`${paths.static.dev}/style`));
});

/*** Watch ***/
gulp.task('browser-sync', () => {
  browserSync.init({
    notify: false,
    proxy: `${config.host}:${config.port}`,
  });
  return $.watch(
    [`${paths.static.dev}/**/*.{css,js}`, `${paths.main}/**/*.{html,py}`],
    {
      events: ['change'],
    },
    file => {
      return browserSync.reload();
    },
  );
});

gulp.task('ext_watch_rebuild', callback => {
  return $.sequence(
    'clean:dev',
    'copy_bower_files',
    'ext:dev',
    'style:dev',
  )(callback);
});

gulp.task('watch', () => {
  $.watch('requirements.txt', () => {
    return $.sequence('pip')();
  });
  $.watch('package.json', () => {
    return $.sequence('yarn')();
  });
  $.watch('bower.json', () => {
    return $.sequence('ext_watch_rebuild')();
  });
  $.watch('gulp/config.js', () => {
    return $.sequence('ext:dev', ['style:dev', 'script:dev'])();
  });
  $.watch(paths.static.ext, () => {
    return $.sequence('ext:dev')();
  });
  $.watch(`${paths.src.script}/**/*.js`, () => {
    return $.sequence('script:dev')();
  });
  return $.watch(`${paths.src.style}/**/*.less`, () => {
    return $.sequence('style:dev')();
  });
});
