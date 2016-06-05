angular.module('configView')
  .component('configView', {
    templateUrl: 'app/config/config-view.template.html',
    controller: ['Config',
      function ConfigListController(Config) {
        var self = this;
        Config.query().$promise.then(function(response) {
          self.config_db = response.result;
        }, function(error) {
          self.error = error;
        });
      }
    ]
  });
