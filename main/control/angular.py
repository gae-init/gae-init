# coding: utf-8

import flask

from main import app


@app.route('/angular/')
def angular():
  return flask.render_template(
    'angular.html',
    title='Angular',
    html_class='angular',
  )
