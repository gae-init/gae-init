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
bower_dir = "#{static_dir}/bower_components"
style_dir = "#{static_dir}/src/style"
script_dir = "#{static_dir}/src/script"

# We handpick the paths in the order we want then to be injected or
# concatenated, when minified.
paths =
  styles: [
    "#{static_dir}/dst/style/style.css"
  ]
  scripts: [
    "#{static_dir}/dst/script/common/service.js"
    "#{static_dir}/dst/script/common/util.js"
    "#{static_dir}/dst/script/site/app.js"
    "#{static_dir}/dst/script/site/admin.js"
    "#{static_dir}/dst/script/site/profile.js"
    "#{static_dir}/dst/script/site/auth.js"
    "#{static_dir}/dst/script/site/user.js"
  ]
  bower_components: [
    "#{bower_dir}/jquery/dist/jquery.js"
    "#{bower_dir}/moment/moment.js"
    "#{bower_dir}/nprogress/nprogress.js"
    "#{bower_dir}/bootstrap-sweetalert/lib/sweet-alert.js"
    "#{bower_dir}/bootstrap/js/alert.js"
    "#{bower_dir}/bootstrap/js/button.js"
    "#{bower_dir}/bootstrap/js/transition.js"
    "#{bower_dir}/bootstrap/js/collapse.js"
    "#{bower_dir}/bootstrap/js/dropdown.js"
    "#{bower_dir}/bootstrap/js/tooltip.js"
  ]
  clean: [
    "#{static_dir}/dst"
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


# Building the style, styles from bower_components are imported in style.less
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


gulp.task 'minify', ->
  del "#{static_dir}/min"
  gulp.src(paths.bower_components)
    .pipe $.plumber()
    .pipe $.concat("libs.min.js")
    .pipe $.uglify()
    .pipe gulp.dest("#{static_dir}/min/script/")

  gulp.src(paths.scripts)
    .pipe $.concat("script.min.js")
    .pipe $.uglify()
    .pipe gulp.dest("#{static_dir}/min/script/")

  gulp.src(paths.styles)
    .pipe $.min_css(keepBreaks: true)
    .pipe gulp.dest("#{static_dir}/min/style/")


gulp.task 'inject', ->
  scripts = gulp.src(paths.scripts, read: false)
  gulp.src("#{root_dir}/templates/bit/script.html")
    .pipe $.inject(gulp.src(paths.bower_components),
      name: 'bower'
      ignorePath: '/main/static'
      addPrefix: '/p'
    )
    .pipe $.inject(scripts,
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


gulp.task 'default', ['reload', 'watch', 'less', 'coffee', 'inject']
gulp.task 'min', ['less', 'coffee', 'minify']
