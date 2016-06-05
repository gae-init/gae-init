angular.module('userList')
  .component('userList', {
    templateUrl: 'app/user/user-list.template.html',
    controller: ['User',
      function UserListController(User) {
        var self = this;
        User.query().$promise.then(function(response) {
          self.user_dbs = response.result;
        }, function(error) {
          self.error = error;
        });
      }
    ]
  });
