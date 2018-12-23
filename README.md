# gae-init

[![Slack Status](https://gae-init-slack.herokuapp.com/badge.svg)](https://gae-init-slack.herokuapp.com) [![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)

> **gae-init** is the easiest boilerplate to kick start new applications on Google App Engine using Python, Flask, RESTful, Bootstrap and tons of other cool features.

Read the [documentation][], where you can find a complete [feature list][], a detailed [tutorial][], the [how to][] section and more..

The latest version is always accessible from [https://gae-init.appspot.com](https://gae-init.appspot.com)

## Requirements

- [Docker][]
- [macOS][] or [Linux][] or [Windows][]

Make sure you have all of the above or refer to the docs on how to [install the requirements](http://docs.gae-init.appspot.com/requirement/).

## Running the Development Environment

```bash
cd /path/to/project-name

docker run --rm -ti \
  -p 8080-8081:8080-8081 \
  -p 3000-3001:3000-3001 \
  -v $PWD:/var/app:cached \
  gmist/gae-init gulp
```

To test it visit [http://localhost:3000](http://localhost:3000) in your browser.

---

For a complete list of commands:

```bash
docker run --rm -ti \
  -v $PWD:/var/app \
  gmist/gae-init gulp help
```

## Initializing or Resetting the project

```bash
cd /path/to/project-name

docker run --rm -ti \
  -p 8080-8081:8080-8081 \
  -p 3000-3001:3000-3001 \
  -v $PWD:/var/app:cached \
  -v $PWD/temp/config:/root/.config \
  gmist/gae-init /bin/sh

gcloud auth login
yarn
gulp
```

If something goes wrong you can always do:

```bash
docker run --rm -ti \
  -p 8080-8081:8080-8081 \
  -p 3000-3001:3000-3001 \
  -v $PWD:/var/app:cached \
  -v $PWD/temp/config:/root/.config \
  gmist/gae-init /bin/sh

gulp reset
yarn
gulp
```

## Local testing

If you wish to run an automated test script, there is an additional dependency which can be installed with:

```bash
docker run --rm -ti \
     -v $PWD:/var/app:cached \
     gmist/gae-init pip install -r test-requirements.txt
```

A simple test script framework, following the approach from the [Google App Engine docs](https://cloud.google.com/appengine/docs/standard/python/tools/localunittesting#setup), can be run:

```bash
docker run --rm -ti \
     -v $PWD:/var/app:cached \
     gmist/gae-init /bin/sh

python main/runner.py --test-path tests /google-cloud-sdk/
```

This simply tests that the site can start up; that the index page exists (and returns an http response code of 200), and that a non-existent page returns an http response code of 404.

The test framework is easily extensible.

## Deploying on Google App Engine

```bash
docker run --rm -ti \
  -v $PWD/temp/config:/root/.config \
  -v $PWD:/var/app:cached \
  gmist/gae-init gulp deploy
```

or

```bash
docker run --rm -ti \
  -v $PWD/temp/config:/root/.config \
  -v $PWD:/var/app:cached \
  gmist/gae-init gulp deploy --project=foo
```

or

```bash
docker run --rm -ti \
  -v $PWD/temp/config:/root/.config \
  -v $PWD:/var/app:cached \
  gmist/gae-init gulp deploy --project=foo --version=bar
```

or

```bash
docker run --rm -ti \
  -v $PWD/temp/config:/root/.config \
  -v $PWD:/var/app:cached \
  gmist/gae-init gulp deploy --project=foo --version=bar --no-promote
```

## Tech Stack

- [Google App Engine][], [NDB][]
- [Jinja2][], [Flask][], [Flask-RESTful][], [Flask-WTF][]
- [Less][]
- [Docker][]
- [Bootstrap][], [Font Awesome][], [Social Buttons][]
- [jQuery][], [Moment.js][]
- [OpenID][] sign in (Google, Facebook, Twitter and more)
- [Python 2.7][], [pip][], [virtualenv][]
- [Gulp][], [Bower][]

[bootstrap]: http://getbootstrap.com/
[bower]: http://bower.io/
[docker]: https://www.docker.com
[documentation]: http://docs.gae-init.appspot.com
[feature list]: http://docs.gae-init.appspot.com/features/
[flask-restful]: https://flask-restful.readthedocs.org
[flask-wtf]: https://flask-wtf.readthedocs.org
[flask]: http://flask.pocoo.org/
[font awesome]: http://fortawesome.github.com/Font-Awesome/
[google app engine]: https://developers.google.com/appengine/
[gulp]: http://gulpjs.com
[how to]: http://docs.gae-init.appspot.com/howto/
[jinja2]: http://jinja.pocoo.org/docs/
[jquery]: https://jquery.com/
[less]: http://lesscss.org/
[linux]: http://www.ubuntu.com
[macos]: http://www.apple.com/macos/
[moment.js]: http://momentjs.com/
[ndb]: https://developers.google.com/appengine/docs/python/ndb/
[openid]: http://en.wikipedia.org/wiki/OpenID
[pip]: http://www.pip-installer.org/
[python 2.7]: https://developers.google.com/appengine/docs/python/python27/using27
[social buttons]: http://lipis.github.io/bootstrap-social/
[tutorial]: http://docs.gae-init.appspot.com/tutorial/
[virtualenv]: http://www.virtualenv.org/
[windows]: http://windows.microsoft.com/
