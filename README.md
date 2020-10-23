# grow-ext-static-server

[![Build Status](https://travis-ci.org/grow/grow-ext-static-server.svg?branch=master)](https://travis-ci.org/grow/grow-ext-static-server)

A zero configuration, localization-aware static server that supports redirects designed to be used with Google App Engine.

## Concept

Many websites display the "Get on Google Play" and "Download on the App Store"
badge images, advertising a mobile app download. This extension simplifies usage
by exposing the correct localized badge image via a YAML configuration file.

The images are included in SVG form with a tightly-cropped view box from:

- [App Store Brand Guidelines](https://developer.apple.com/app-store/marketing/guidelines/#section-badges)
- [Google Play Badge Generator](https://play.google.com/intl/en_us/badges/)

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