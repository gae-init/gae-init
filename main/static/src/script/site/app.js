'use strict';

$(() => {
  initCommon();
});

$(() => {
  $('html.auth').each(() => {
    initAuth();
  });
});

$(() => {
  $('html.user-list').each(() => {
    initUserList();
  });
});

$(() => {
  $('html.user-merge').each(() => {
    init_user_merge();
  });
});
