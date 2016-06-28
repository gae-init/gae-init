paths = require './paths'

config =
  ext: [
    "#{paths.dep.node_modules}/jquery/dist/jquery.js"
    "#{paths.dep.node_modules}/moment/moment.js"
    "#{paths.dep.node_modules}/bootstrap/js/alert.js"
    "#{paths.dep.node_modules}/bootstrap/js/button.js"
    "#{paths.dep.node_modules}/bootstrap/js/transition.js"
    "#{paths.dep.node_modules}/bootstrap/js/collapse.js"
    "#{paths.dep.node_modules}/bootstrap/js/dropdown.js"
    "#{paths.dep.node_modules}/bootstrap/js/tooltip.js"
  ]
  style: [
    "#{paths.src.style}/style.less"
  ]
  script: [
    "#{paths.src.script}/**/*.coffee"
    "#{paths.src.script}/**/*.js"
  ]

module.exports = config
