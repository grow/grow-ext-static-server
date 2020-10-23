# grow-ext-static-server

[![Build Status](https://travis-ci.org/grow/grow-ext-static-server.svg?branch=master)](https://travis-ci.org/grow/grow-ext-static-server)

A zero configuration, localization-aware static server that supports redirects designed to be used with Google App Engine.

## Concept

Many static websites require limited dynamic functionality such as:

- Vanity URL redirects
- Trailing slash normalization
- Localization (via redirects or rewriting responses)

This utility provides the above limited functionality in a zero-configuration manner, compatible with the `podspec.yaml` syntax for Grow websites and an additional redirect configuration file.

## Usage

### Grow setup

1. Create an `extensions.txt` file within your pod.
1. Add to the file: `git+git://github.com/grow/grow-ext-static-server`
1. Run `grow install`.
1. Add an `app.yaml` file to the project root:

```yaml
runtime: python37
entrypoint: gunicorn -b :8080 -w 2 extensions.grow_static_server.main:app

handlers:
- url: (.*)
  script: auto
  secure: always
```