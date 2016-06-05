paths = require './paths'

config =
  ext: [
    "#{paths.static.ext}/jquery/dist/jquery.js"
    "#{paths.static.ext}/moment/moment.js"
    "#{paths.static.ext}/angular/angular.js"
    "#{paths.static.ext}/angular-moment/angular-moment.js"
    "#{paths.static.ext}/angular-resource/angular-resource.js"
    "#{paths.static.ext}/angular-route/angular-route.js"
    "#{paths.static.ext}/bootstrap/js/alert.js"
    "#{paths.static.ext}/bootstrap/js/button.js"
    "#{paths.static.ext}/bootstrap/js/transition.js"
    "#{paths.static.ext}/bootstrap/js/collapse.js"
    "#{paths.static.ext}/bootstrap/js/dropdown.js"
    "#{paths.static.ext}/bootstrap/js/tooltip.js"
  ]
  style: [
    "#{paths.src.style}/style.less"
  ]
  script: [
    "#{paths.src.script}/**/*.coffee"
    "#{paths.src.script}/**/*.module.js"
    "#{paths.src.script}/**/*.js"
    "#{paths.src.script}/**/*.html"
  ]

module.exports = config
