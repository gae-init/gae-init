'use strict';

window.init_auth = () => {
  $('.remember').change(() => {
    let href;
    let buttons = $('.btn-social').toArray().concat($('.btn-social-icon').toArray());
    let remember = $('.remember input').is(':checked');
    for (let button of buttons) {
      href = $(button).prop('href');
      if (remember) {
        $(button).prop('href', `${href}&remember=true`);
      } else {
        $(button).prop('href', href.replace('&remember=true', ''));
      }
    }
  });
  $('.remember').change();
};
