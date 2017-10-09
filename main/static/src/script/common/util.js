'use strict';

window.LOG = function() {
  typeof console !== 'undefined' && console !== null
    ? typeof console.log === 'function' ? console.log(...arguments) : void 0
    : void 0;
};

window.init_common = () => {
  init_loading_button();
  init_confirm_button();
  init_password_show_button();
  init_time();
  init_announcement();
  init_row_link();
};

window.init_loading_button = () =>
  $('body').on('click', '.btn-loading', function() {
    $(this).button('loading');
  });

window.init_confirm_button = () =>
  $('body').on('click', '.btn-confirm', function() {
    if (!confirm($(this).data('message') || 'Are you sure?')) {
      event.preventDefault();
    }
  });

window.init_password_show_button = () =>
  $('body').on('click', '.btn-password-show', function() {
    let $target;
    $target = $($(this).data('target'));
    $target.focus();
    if ($(this).hasClass('active')) {
      $target.attr('type', 'password');
    } else {
      $target.attr('type', 'text');
    }
  });

window.init_time = () => {
  let recalculate;
  if ($('time').length > 0) {
    recalculate = function() {
      $('time[datetime]').each(function() {
        let date;
        let diff;
        date = moment.utc($(this).attr('datetime'));
        diff = moment().diff(date, 'days');
        if (diff > 25) {
          $(this).text(date.local().format('YYYY-MM-DD'));
        } else {
          $(this).text(date.fromNow());
        }
        $(this).attr('title', date.local().format('dddd, MMMM Do YYYY, HH:mm:ss Z'));
      });
      setTimeout(arguments.callee, 1000 * 45);
    };
    recalculate();
  }
};

window.init_announcement = () => {
  $('.alert-announcement button.close').click(
    () =>
      typeof sessionStorage !== 'undefined' && sessionStorage !== null
        ? sessionStorage.setItem('closedAnnouncement', $('.alert-announcement').html())
        : void 0,
  );
  if (
    (typeof sessionStorage !== 'undefined' && sessionStorage !== null
      ? sessionStorage.getItem('closedAnnouncement')
      : void 0) !== $('.alert-announcement').html()
  ) {
    $('.alert-announcement').show();
  }
};

window.init_row_link = () => {
  $('body').on('click', '.row-link', function() {
    window.location.href = $(this).data('href');
  });
  $('body').on('click', '.not-link', event => event.stopPropagation());
};

window.clear_notifications = () => $('#notifications').empty();

window.show_notification = (message, category) => {
  if (category == null) {
    category = 'warning';
  }
  clear_notifications();
  if (!message) {
    return;
  }
  $('#notifications').append(
    `<div class="alert alert-dismissable alert-${category}"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>${message}</div>`,
  );
};
