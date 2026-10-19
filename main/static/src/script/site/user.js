window.initUserList = () => {
  initUserSelections();
  initUserDeleteBtn();
  initUserMergeBtn();
};

const initUserSelections = () => {
  document.querySelectorAll('input[name=user_db]').forEach((el) => {
    userSelectRow(el);
    el.addEventListener('change', () => {
      userSelectRow(el);
    });
  });

  const selectAll = document.getElementById('select-all');
  if (selectAll) {
    selectAll.addEventListener('change', (event) => {
      const isChecked = event.target.checked;
      document.querySelectorAll('input[name=user_db]').forEach((el) => {
        el.checked = isChecked;
        userSelectRow(el);
      });
    });
  }
};

const userSelectRow = (element) => {
  updateUserSelections();
  const id = element.value;
  const row = document.getElementById(id);
  if (row) {
    if (element.checked) {
      row.classList.add('table-warning');
    } else {
      row.classList.remove('table-warning');
    }
  }
};

const updateUserSelections = () => {
  const selectedCount = document.querySelectorAll(
    'input[name=user_db]:checked',
  ).length;
  const totalCount = document.querySelectorAll('input[name=user_db]').length;

  const userActions = document.getElementById('user-actions');
  if (userActions) {
    userActions.classList.toggle('d-none', selectedCount === 0);
  }

  const userMerge = document.getElementById('user-merge');
  if (userMerge) {
    const mergeItem = userMerge.closest('li') || userMerge;
    mergeItem.classList.toggle('d-none', selectedCount < 2);
  }

  const selectAll = document.getElementById('select-all');
  if (selectAll) {
    if (selectedCount === 0) {
      selectAll.indeterminate = false;
      selectAll.checked = false;
    } else if (selectedCount === totalCount) {
      selectAll.indeterminate = false;
      selectAll.checked = true;
    } else {
      selectAll.indeterminate = true;
    }
  }
};

const initUserDeleteBtn = () => {
  const deleteBtn = document.getElementById('user-delete');
  if (!deleteBtn) {
    return;
  }

  deleteBtn.addEventListener('click', async function (event) {
    clearNotifications();
    event.preventDefault();
    const checkedBoxes = document.querySelectorAll(
      'input[name=user_db]:checked',
    );
    const selectedCount = checkedBoxes.length;
    const confirmMessage = (this.getAttribute('data-confirm') || '').replace(
      '{users}',
      selectedCount,
    );

    if (confirm(confirmMessage)) {
      const user_keys = [];
      checkedBoxes.forEach((el) => {
        el.disabled = true;
        user_keys.push(el.value);
      });

      const deleteUrl = this.getAttribute('data-api-url');
      const successMessage = this.getAttribute('data-success');
      const errorMessage = this.getAttribute('data-error');

      try {
        await apiCall('DELETE', deleteUrl, {user_keys: user_keys.join(',')});

        user_keys.forEach((id) => {
          const row = document.getElementById(id);
          if (row) {
            row.remove();
          }
        });

        updateUserSelections();
        showNotification(
          (successMessage || '').replace('{users}', user_keys.length),
          'success',
        );
      } catch (error) {
        LOG('User delete failed', error);
        document
          .querySelectorAll('input[name=user_db]:disabled')
          .forEach((el) => (el.disabled = false));
        showNotification(
          (errorMessage || '').replace('{users}', user_keys.length),
          'danger',
        );
      }
    }
  });
};

window.initUserMerge = async () => {
  const userKeysInput = document.getElementById('user_keys');
  if (!userKeysInput) {
    return;
  }

  const user_keys = userKeysInput.value;
  const apiUrlElement = document.querySelector('.api-url');
  if (!apiUrlElement) {
    return;
  }

  const api_url = apiUrlElement.getAttribute('data-api-url');

  try {
    const {result} = await apiCall('GET', api_url, {user_keys});
    window.user_dbs = result;
    document
      .querySelectorAll('input[name=user_db]')
      .forEach((el) => (el.disabled = false));
  } catch (error) {
    LOG('Something went terribly wrong', error);
  }

  document.querySelectorAll('input[name=user_db]').forEach((el) => {
    el.addEventListener('change', (event) => {
      const user_key = event.currentTarget.value;
      selectDefaultUser(user_key);
    });
  });
};

const selectDefaultUser = (user_key) => {
  document.querySelectorAll('.user-row').forEach((row) => {
    row.classList.remove('table-success');
    row.classList.add('table-danger');
  });

  const activeRow = document.getElementById(user_key);
  if (activeRow) {
    activeRow.classList.remove('table-danger');
    activeRow.classList.add('table-success');
  }

  for (const user_db of window.user_dbs || []) {
    if (user_key === user_db.key) {
      document.querySelector('input[name=user_key]').value = user_db.key;
      document.querySelector('input[name=username]').value = user_db.username;
      document.querySelector('input[name=name]').value = user_db.name;
      document.querySelector('input[name=email]').value = user_db.email;
      break;
    }
  }
};

const initUserMergeBtn = () => {
  const mergeBtn = document.getElementById('user-merge');
  if (!mergeBtn) {
    return;
  }

  mergeBtn.addEventListener('click', function (event) {
    event.preventDefault();
    const user_keys = Array.from(
      document.querySelectorAll('input[name=user_db]:checked'),
    ).map((el) => el.value);
    const user_merge_url = this.getAttribute('data-user-merge-url');
    window.location.href = `${user_merge_url}?user_keys=${user_keys.join(',')}`;
  });
};
