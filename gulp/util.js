(function () {
  // eslint-disable-next-line
  $ = require('gulp-load-plugins')();

  const onError = function (err) {
    $.util.beep();
    console.log(err);
    return this.emit('end');
  };

  module.exports = {onError};
}.call(this));
