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
2. Add to the file: `git+git://github.com/grow/grow-ext-static-server`
3. Run `grow install`.
4. Add `requirements.txt` to the project root:

```txt
gunicorn
pyyaml
webapp2==3.0.0b1
```

5. Add an `app.yaml` file to the project root:

```yaml
# app.yaml
runtime: python37
entrypoint: gunicorn -b :$PORT -w 2 extensions.grow_static_server.main:app

handlers:
- url: (.*)
  script: auto
  secure: always
```

6. Add a `.gcloudignore` file to the project root:

```txt
*
!/build/**
!/extensions/**
!/podspec.yaml
!/redirects.py
!/redirects.yaml
!/requirements.txt
!.
```

### Configure and deploy

7. Optionally add redirects, via `redirects.yaml` in the project root:

```yaml
# redirects.yaml

redirects:
- ['/vanity-url', '/some-much-longer-destination-url']
- ['/test', 'https://example.com/']
- ['/test/:foo', 'https://example.com/$foo']

settings:
  rewrite_localized_content: true  # Either true (default) or false.
  trailing_slash_behavior: add  # Either 'add' (default) or 'remove'.
```

8. Deploy the application. See [Makefile](test/Makefile) for example deployment commands.
