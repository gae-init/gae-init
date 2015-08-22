paths = require './paths'

config =
  host: "127.0.0.1"
  port: "8080"
  ext: [
    "#{paths.static.ext}/jquery/dist/jquery.js"
    "#{paths.static.ext}/moment/moment.js"
    "#{paths.static.ext}/bootstrap/dist/js/bootstrap.js"
  ]
  style: [
    "#{paths.src.style}/style.scss"
  ]
  script: [
    "#{paths.src.script}/**/*.coffee"
    "#{paths.src.script}/**/*.js"
  ]


module.exports = config
