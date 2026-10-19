window.LOG = function () {
  return typeof console !== 'undefined' && console !== null
    ? typeof console.log === 'function'
      ? console.log(...arguments)
      : void 0
    : void 0;
};

window.initCommon = () => {
  initLoadingButton();
  initConfirmButton();
  initPasswordShowButton();
  initTime();
  initAnnouncement();
  initRowLink();
  initCardCollapse();
  initDateInputs();
};

window.initLoadingButton = () => {
  const applyLoadingState = (btn) => {
    if (!btn || btn.dataset.loadingApplied) {
      return;
    }
    btn.dataset.loadingApplied = 'true';
    setTimeout(() => {
      btn.disabled = true;
      const text = btn.getAttribute('data-loading-text') || 'Loading...';
      if (text) {
        btn.innerHTML = text;
      }
    }, 0);
  };

  document.body.addEventListener('click', (event) => {
    const btn = event.target.closest('.btn-loading');
    if (btn) {
      applyLoadingState(btn);
    }
  });

  document.body.addEventListener('submit', (event) => {
    if (event.defaultPrevented) {
      return;
    }
    const btn = event.target.querySelector(
      '.btn-loading[type="submit"], button.btn-loading:not([type])',
    );
    if (btn) {
      applyLoadingState(btn);
    }
  });
};

window.initConfirmButton = () => {
  document.body.addEventListener('click', (event) => {
    const btn = event.target.closest('.btn-confirm');
    if (btn) {
      if (!confirm(btn.getAttribute('data-message') || 'Are you sure?')) {
        event.preventDefault();
      }
    }
  });
};

window.initPasswordShowButton = () => {
  document.body.addEventListener('click', (event) => {
    const btn = event.target.closest('.btn-password-show');
    if (btn) {
      const targetSelector =
        btn.getAttribute('data-bs-target') || btn.getAttribute('data-target');
      const target = document.querySelector(targetSelector);
      if (target) {
        target.focus();
        const icon = btn.querySelector('.fa');
        const isHidden = target.getAttribute('type') === 'password';
        if (isHidden) {
          target.setAttribute('type', 'text');
          btn.classList.add('active');
          if (icon) {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
          }
        } else {
          target.setAttribute('type', 'password');
          btn.classList.remove('active');
          if (icon) {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
          }
        }
      }
    }
  });
};

window.initTime = () => {
  if (document.querySelectorAll('time').length > 0) {
    dayjs.extend(window.dayjs_plugin_utc);
    dayjs.extend(window.dayjs_plugin_relativeTime);
    dayjs.extend(window.dayjs_plugin_advancedFormat);

    const recalculate = function () {
      document.querySelectorAll('time[datetime]').forEach((el) => {
        const date = dayjs.utc(el.getAttribute('datetime'));
        const diff = dayjs().diff(date, 'days');
        if (diff > 25) {
          el.textContent = date.local().format('YYYY-MM-DD');
        } else {
          el.textContent = date.fromNow();
        }
        el.setAttribute(
          'title',
          date.local().format('dddd, MMMM Do YYYY, HH:mm:ss Z'),
        );
      });
      setTimeout(recalculate, 1000 * 45);
    };
    recalculate();
  }
};

window.initAnnouncement = () => {
  const alertAnnouncements = document.querySelectorAll('.alert-announcement');
  alertAnnouncements.forEach((alert) => {
    const closeBtn = alert.querySelector('.btn-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        if (typeof sessionStorage !== 'undefined' && sessionStorage !== null) {
          sessionStorage.setItem('closedAnnouncement', alert.innerHTML);
        }
      });
    }

    if (
      (typeof sessionStorage !== 'undefined' && sessionStorage !== null
        ? sessionStorage.getItem('closedAnnouncement')
        : void 0) !== alert.innerHTML
    ) {
      alert.style.display = 'block';
    }
  });
};

window.initRowLink = () => {
  const handleRowClick = (event) => {
    const rowLink = event.target.closest('.row-link');
    const notLink = event.target.closest('.not-link, a, button, input, label');

    if (notLink) {
      return;
    }
    if (rowLink) {
      const href = rowLink.getAttribute('data-href');
      if (href) {
        if (event.ctrlKey || event.metaKey || event.button === 1) {
          window.open(href, '_blank');
        } else if (event.button === 0) {
          window.location.href = href;
        }
      }
    }
  };

  document.body.addEventListener('click', handleRowClick);
  document.body.addEventListener('auxclick', handleRowClick);
};

window.initCardCollapse = () => {
  document.body.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      const toggle = event.target.closest(
        '.card-header[data-bs-toggle="collapse"]',
      );
      if (toggle && event.target === toggle) {
        event.preventDefault();
        toggle.click();
      }
    }
  });
};

window.initDateInputs = () => {
  const updateDateEmpty = (el) => {
    if (
      el &&
      el.matches &&
      el.matches('input[type="date"], input[type="datetime-local"]')
    ) {
      el.classList.toggle('is-empty', !el.value);
    }
  };

  document
    .querySelectorAll('input[type="date"], input[type="datetime-local"]')
    .forEach(updateDateEmpty);

  document.body.addEventListener('input', (event) => {
    updateDateEmpty(event.target);
  });
  document.body.addEventListener('change', (event) => {
    updateDateEmpty(event.target);
  });
};

window.clearNotifications = () => {
  const container = document.getElementById('notifications');
  if (container) {
    container.innerHTML = '';
  }
};

window.showNotification = (message, category = 'warning') => {
  clearNotifications();
  if (!message) {
    return;
  }
  const container = document.getElementById('notifications');
  if (container) {
    container.insertAdjacentHTML(
      'beforeend',
      `<div class="alert alert-dismissible alert-${category}"><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>${message}</div>`,
    );
  }
};
