/* eslint-disable id-length */

const gulp = require('gulp-help')(require('gulp'));
const yargs = require('yargs-parser');
const $ = require('gulp-load-plugins')();
const config = require('../config');
const paths = require('../paths');

gulp.task(
  'build',
  `Build project to prepare it for a deployment. Minify CSS & JS files and pack Python dependencies into ${paths.py.lib_file}.`,
  $.sequence('clean:min', 'init', 'ext', 'script', 'style', 'zip'),
);

gulp.task(
  'rebuild',
  'Re-build project from scratch. Equivalent to "reset" and "build" tasks.',
  $.sequence('reset', 'build'),
);

gulp.task(
  'deploy',
  'Deploy project to Google App Engine. Available options:',
  ['build'],
  () => {
    const options = yargs(process.argv, {
      configuration: {
        'boolean-negation': false,
        'camel-case-expansion': false,
      },
    });
    delete options._;
    let options_str = '';
    let dryrun = '';
    for (const index in options) {
      if (index === 'dryrun') {
        dryrun = 'echo DRYRUN - would run: ';
      } else {
        if (options[index] === true) {
          options[index] = '';
        }
        options_str +=
          ' ' +
          (index.length > 1 ? '-' : '') +
          '-' +
          index +
          ' ' +
          options[index];
      }
    }
    return gulp.src('run.py').pipe(
      $.start([
        {
          cmd: dryrun + 'gcloud app deploy main/*.yaml' + options_str,
          match: /run.py$/,
        },
      ]),
    );
  },
  {
    options: {
      dryrun: 'run all preparations but do not actually deploy',
    },
  },
);

gulp.task(
  'run',
  'Start the local server. Available options:\n -o HOST  - the host to start the dev_appserver.py\n -p PORT  - the port to start the dev_appserver.py\n -a="..." - all following args are passed to dev_appserver.py\n',
  () => {
    return $.sequence('init', ['ext:dev', 'script:dev', 'style:dev'])(() => {
      const argv = process.argv.slice(2);
      const known_options = {
        default: {
          a: '',
          o: '',
          p: '',
        },
      };
      const options = yargs(argv);
      let options_str = '-s';
      for (const index in known_options.default) {
        if (options[index]) {
          if (index === 'a') {
            options_str += ' --appserver-args "' + options[index] + '"';
          } else {
            options_str += ' -' + index + ' ' + options[index];
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
            cmd: 'python run.py ' + options_str,
            match: /run.py$/,
          },
        ]),
      );
    });
  },
);
