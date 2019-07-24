const $ = require('gulp-load-plugins')();

const onError = function(err) {
  $.util.beep();
  console.log(err);
  this.emit('end');
};

module.exports = {
  onError: onError,
};
