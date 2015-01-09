gulp = require('gulp')
$ = require('gulp-load-plugins')(
  rename:
    'gulp-minify-css': 'min_css'
)
main_bower_files = require 'main-bower-files'
del = require 'del'
exec = require('child_process').exec
minimist = require 'minimist'

root_dir = './main'
static_dir = "#{root_dir}/static"
paths =
  clean: [
      "#{static_dir}/dst"
      "#{static_dir}/ext"
      "#{static_dir}/min"
    ]
  watch: [
      "#{static_dir}/dst/style/**/*.css"
      "#{static_dir}/dst/script/**/*.js"
      "#{static_dir}/src/**/*.less"
      "#{root_dir}/**/*.html"
      "#{root_dir}/**/*.py"
    ]


run = (option) ->
  proc = exec "python -u run.py -#{option}"
  proc.stderr.on 'data', (data) -> process.stderr.write data
  proc.stdout.on 'data', (data) -> process.stdout.write data

gulp.task 'clean', ->
  del paths.clean

gulp.task 'bower_install', ->
  $.bower()

gulp.task 'ext', ['bower_install'], ->
  gulp.src(main_bower_files(),
    base: 'bower_components'
  ).pipe gulp.dest("#{static_dir}/ext")

gulp.task 'less', ->
  gulp.src("#{static_dir}/src/style/style.less")
    .pipe $.plumber()
    .pipe $.less()
    .pipe gulp.dest("#{static_dir}/dst/style/")
    .pipe $.min_css(keepBreaks: true)
    .pipe gulp.dest("#{static_dir}/min/style/")

gulp.task 'reload', ->
  $.livereload.listen()
  gulp.watch(paths.watch).on 'change', $.livereload.changed

gulp.task 'watch', ->
  gulp.watch("#{static_dir}/src/style/**/*.less", ['less'])
  # run 'w'

gulp.task 'run', ->
  argv = process.argv.slice(2)
  argv_lenght = Object.keys(argv).length
  if argv_lenght <= 1
    run 's'
  else
    known_options =
      default:
        C: false
        c: false
        h: false
        m: false
        s: false
        w: false
    options = minimist argv, known_options
    for k of known_options.default
      if options[k]
        run k
        break

gulp.task 'default', ['reload', 'watch', 'less']
