'use strict';

angular.module('core.config')
  .factory('Config', ['$resource',
    function($resource) {
      return $resource('/api/v1/admin/config/', {}, {
        query: {
          method: 'GET',
          cache: true
        }
      });
    }
  ]);
