document.addEventListener('DOMContentLoaded', () => {
  initCommon();

  document.querySelectorAll('html.auth').forEach(() => {
    initAuth();
  });

  document.querySelectorAll('html.user-list').forEach(() => {
    initUserList();
  });

  document.querySelectorAll('html.user-merge').forEach(() => {
    initUserMerge();
  });
});
