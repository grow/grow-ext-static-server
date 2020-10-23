"""Main entrypoint for web server application."""

from .locale_redirect_middleware import LocaleRedirectMiddleware
from .redirect_middleware import RedirectMiddleware
import logging
import mimetypes
import os
import webapp2
import yaml

podspec_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'podspec.yaml'))
podspec = yaml.safe_load(open(podspec_path, encoding='utf-8'))
default_locale = podspec.get('localization', {}).get('default_locale', 'en')
www_root = './build' + podspec.get('root', '/')
pod_root = podspec.get('root', '/')
locales = podspec.get('localization', {}).get('locales', [])

# Whether to rewrite root URLs with localized content, resulting in
# fallback for localized content. Ensure requests are not cached.
rewrite_content = True

mimetypes.add_type('text/template', '.mustache')


class StaticHandler(webapp2.RequestHandler):
  """Abstract class to handle serving static files."""

  def get(self, path=''):
    path = path.lstrip('/')
    path = os.path.join(os.path.dirname(__file__), 'build', path)

    if os.path.isdir(path):
      path = path.rstrip('/') + '/index.html'

    logging.info('Serving -> {}'.format(path))

    if not os.path.isfile(path):
      webapp2.abort(404)

    mimetype = mimetypes.guess_type(path)[0] or 'text/plain'
    self.response.headers['Content-Type'] = mimetype
    fp = open(path, 'rb')
    # Bypass the subclass's `write` method due to Python 3 incompatibility.
    # https://github.com/GoogleCloudPlatform/webapp2/issues/146
    super(webapp2.Response, self.response).write(fp.read())


class TrailingSlashRedirect(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        base, ext = os.path.splitext(os.path.basename(path))

        # /index.html -> / redirect.
        if path.endswith('/index.html'):
            path = path[:-11]
            path = '/{}'.format(path)
            status = '302 Found'
            response_headers = [('Location', path)]
            start_response(status, response_headers)
            return []

        # /foo -> /foo/ redirect.
        if base and not ext:
            path = '{}/'.format(path)
            status = '302 Found'
            response_headers = [('Location', path)]
            start_response(status, response_headers)
            return []

        return self.app(environ, start_response)



def app(_, request):
  local_app = webapp2.WSGIApplication([
      ('(.*)', StaticHandler),
  ])
  local_app = LocaleRedirectMiddleware(
	local_app, www_root=www_root, pod_root=pod_root,
        locales=locales, default_locale=default_locale,
        rewrite_content=rewrite_content)
  local_app = TrailingSlashRedirect(local_app)
  local_app = RedirectMiddleware(local_app)
  return local_app(_, request)
