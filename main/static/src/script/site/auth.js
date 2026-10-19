window.initAuth = () => {
  const handleRememberChange = () => {
    const buttons = [
      ...document.querySelectorAll('.btn-social'),
      ...document.querySelectorAll('.btn-social-icon'),
    ];
    const rememberCheckbox = document.querySelector('.remember input');
    const remember = rememberCheckbox ? rememberCheckbox.checked : false;

    for (const button of buttons) {
      if (!button.href || button.href.startsWith('javascript:')) {
        continue;
      }

      const url = new URL(button.href, window.location.origin);
      if (remember) {
        url.searchParams.set('remember', 'true');
      } else {
        url.searchParams.delete('remember');
      }
      button.href = url.toString();
    }
  };

  document.querySelectorAll('.remember input').forEach((el) => {
    el.addEventListener('change', handleRememberChange);
  });

  handleRememberChange();
};
