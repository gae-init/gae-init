// Generated by CoffeeScript 1.3.1
(function() {

  $(function() {
    return LOG('app init');
  });

  $(function() {
    return $('html.welcome').each(function() {
      return LOG('init welcome');
    });
  });

  $(function() {
    return $('html.profile').each(function() {
      return init_profile();
    });
  });

  $(function() {
    return $('html.admin-config').each(function() {
      return init_admin_config();
    });
  });

}).call(this);
