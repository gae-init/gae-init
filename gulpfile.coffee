gulp = require('gulp')
$ = require('gulp-load-plugins')(
  rename:
    'gulp-minify-css': 'min_css'
)
main_bower_files = require 'main-bower-files'
del = require 'del'
exec = require('child_process').exec

root_dir = './main'
static_dir = "#{root_dir}/static"
style_dir = "#{static_dir}/src/style"
script_dir = "#{static_dir}/src/script"
paths =
  clean: [
      "#{static_dir}/dst"
      "#{static_dir}/ext"
      "#{static_dir}/min"
    ]
  watch: [
      "#{static_dir}/dst/style/**/*.css"
      "#{static_dir}/dst/script/**/*.js"
      "#{root_dir}/**/*.html"
      "#{root_dir}/**/*.py"
    ]

gulp.task 'clean', ->
  del paths.clean

gulp.task 'bower_install', ->
  $.bower()

gulp.task 'ext', ['bower_install'], ->
  gulp.src(main_bower_files(),
    base: 'bower_components'
  ).pipe gulp.dest("#{static_dir}/ext")

gulp.task 'less', ->
  gulp.src("#{style_dir}/style.less")
    .pipe $.plumber()
    .pipe $.less()
    .pipe gulp.dest("#{static_dir}/dst/style/")
    .pipe $.min_css(keepBreaks: true)
    .pipe gulp.dest("#{static_dir}/min/style/")

gulp.task 'coffee', ->
  gulp.src("#{script_dir}/**/*.coffee")
    .pipe $.plumber()
    .pipe $.coffee(bare:true)
    .pipe gulp.dest("#{static_dir}/dst/script/")
    .pipe $.concat("script.min.js")
    .pipe $.uglify()
    .pipe gulp.dest("#{static_dir}/min/script/")

gulp.task 'inject', ->
  sources = gulp.src("#{static_dir}/dst/script/**/*.js",
    read: false
  )
  gulp.src("#{root_dir}/templates/bit/script.html")
    .pipe $.inject(sources,
      ignorePath: '/main/static'
      addPrefix: '/p'
    )
    .pipe gulp.dest("#{root_dir}/templates/bit/")

gulp.task 'reload', ->
  $.livereload.listen()
  gulp.watch(paths.watch).on 'change', $.livereload.changed

gulp.task 'watch', ->
  gulp.watch("#{style_dir}/**/*.less", ['less'])
  gulp.watch("#{script_dir}/**/*.coffee", ['coffee'])

gulp.task 'default', ['reload', 'watch', 'less', 'coffee']
