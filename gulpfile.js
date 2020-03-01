const gulp = require('gulp');

const server = require('browser-sync').create();

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

/*** Script ***/
is_coffee = function(file) {
  return file.path.indexOf('.coffee') > 0;
};

gulp.task('script', () => {
  return gulp
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
    .pipe($.if(is_coffee, $.coffee()))
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
    .pipe(gulp.dest(`${paths.static.dev}/style`))
    .pipe(server.stream());
});

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

gulp.task(
  'copy_bower_files',
  gulp.series('bower', () => {
    return gulp
      .src(main_bower_files(), {
        base: paths.dep.bower_components,
      })
      .pipe(gulp.dest(paths.static.ext));
  }),
);

gulp.task('init', gulp.parallel('pip', 'copy_bower_files'));

// browserSync task
gulp.task('browserSync', () => {
  server.init({
    notify: false,
    proxy: `${config.host}:${config.port}`,
  });
});

/**
  Start the local server. Available options:
  @task {run}
  @arg {-o HOST} the host to start the dev_appserver.py
  @arg {-p PORT} the port to start the dev_appserver.py
  @arg {-a="..."} all following args are passed to dev_appserver.py
  **/
gulp.task(
  'run',
  gulp.series(
    'init',
    gulp.parallel('ext:dev', 'script:dev', 'style:dev'),
    gulp.parallel('browserSync', () => {
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
      //gulp.start('browser-sync');
      return gulp.src('run.py').pipe(
        $.start([
          {
            cmd: `python run.py ${options_str}`,
            match: /run.py$/,
          },
        ]),
      );
    }),
  ),
);

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

gulp.task('clean:dev', () => {
  del(paths.static.ext);
  return del(paths.static.dev);
});

gulp.task('clean:min', () => {
  del(paths.static.ext);
  return del(paths.static.min);
});

gulp.task('clean:venv', () => {
  del(paths.py.lib);
  del(paths.py.lib_file);
  del(paths.dep.py);
  return del(paths.dep.py_guard);
});

/**
Complete reset of project. Run "yarn install" after this procedure.
@task {reset}
**/
gulp.task(
  'reset',
  gulp.series(
    gulp.parallel('clean', 'clean:dev', 'clean:min', 'clean:venv'),
    () => {
      del(paths.dep.bower_components);
      return del(paths.dep.node_modules);
    },
  ),
);

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

gulp.task('zip', done => {
  if (!fs.existsSync(paths.py.lib_file)) {
    if (fs.existsSync(paths.py.lib)) {
      gulp
        .src(`${paths.py.lib}/**`)
        .pipe($.plumber())
        .pipe($.zip('lib.zip'))
        .pipe(gulp.dest(paths.main));
    }
  }
  done();
});

/*** Watch ***/

function reload(done) {
  server.reload();
  done();
}

gulp.task('ext_watch_rebuild', callback => {
  return gulp.parallel(
    'copy_bower_files',
    gulp.series('clean:dev', gulp.parallel('ext:dev', 'style:dev')),
  )(callback);
});

gulp.task('watch', () => {
  $.watch('requirements.txt', () => {
    return gulp.series('pip')();
  });
  $.watch('package.json', () => {
    return gulp.series('yarn')();
  });
  $.watch('bower.json', () => {
    return gulp.series('ext_watch_rebuild')();
  });
  $.watch('gulp/config.js', () => {
    return gulp.series('ext:dev', gulp.parallel('style:dev', 'script:dev'))();
  });
  $.watch(paths.static.ext, () => {
    return gulp.series('ext:dev')();
  });
  $.watch(`${paths.src.script}/**/*.{coffee,js}`, () => {
    return gulp.series('script:dev')();
  });
  $.watch(
    [`${paths.static.dev}/**/*.js`, `${paths.main}/**/*.{html,py}`],
    () => {
      return gulp.series(reload)();
    },
  );
  return $.watch(`${paths.src.style}/**/*.less`, () => {
    return gulp.series('style:dev')();
  });
});

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
  gulp.series(
    'clean:min',
    'init',
    'ext',
    gulp.parallel('script', 'style', 'zip'),
  ),
);

/*
  Re-build project from scratch. Equivalent to "reset" and "build" tasks.
  @task {rebuild}
  */
gulp.task('rebuild', gulp.series('reset', 'build'));

/**
  Deploy project to Google App Engine.
  @task {deploy}
  **/
gulp.task(
  'deploy',
  gulp.series('build', () => {
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
  }),
);

/**
 * Start the local server, watch for changes and reload browser automatically.
 * For available options refer to "run" task.
 * @task {default}
 * @order {1}
 */
gulp.task('default', gulp.parallel('run', 'watch'));
