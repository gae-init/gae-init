'use strict';

angular.module('core.user')
  .factory('User', ['$resource',
    function($resource) {
      return $resource('/api/v1/admin/user/', {}, {
        query: {
          method: 'GET',
          cache: true
        }
      });
    }
  ]);
