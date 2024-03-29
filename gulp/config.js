(function () {
  const paths = require('./paths');

  const config = {
    ext: [
      `${paths.static.ext}/jquery/dist/jquery.js`,
      `${paths.static.ext}/moment/moment.js`,
      `${paths.static.ext}/bootstrap/js/alert.js`,
      `${paths.static.ext}/bootstrap/js/button.js`,
      `${paths.static.ext}/bootstrap/js/transition.js`,
      `${paths.static.ext}/bootstrap/js/collapse.js`,
      `${paths.static.ext}/bootstrap/js/dropdown.js`,
      `${paths.static.ext}/bootstrap/js/tooltip.js`,
    ],
    host: '127.0.0.1',
    port: '8080',
    script: [`${paths.src.script}/**/*.js`, `${paths.src.script}/**/*.coffee`],
    style: [`${paths.src.style}/style.less`],
  };

  module.exports = config;
}.call(this));
