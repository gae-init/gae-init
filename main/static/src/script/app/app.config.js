'use strict';

angular.module('mainApp')
  .config(['$locationProvider' ,'$routeProvider',
    function config($locationProvider, $routeProvider) {
      $locationProvider.hashPrefix('!');
      $routeProvider
        .when('/admin/config/', {
          template: '<config-view></config-view>'
        })
        .when('/admin/user/', {
          template: '<user-list></user-list>'
        })
        .otherwise('/admin/config/');
    }
  ]);
