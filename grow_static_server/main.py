"""Main entrypoint for web server application."""

from .locale_redirect_middleware import LocaleRedirectMiddleware
from .redirect_middleware import RedirectMiddleware
import logging
import mimetypes
import os
import webapp2
import yaml

pod_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
pod_root_path = os.getenv('GROW_STATIC_SERVER_POD_ROOT') or pod_root_path
podspec_path = os.path.abspath(os.path.join(pod_root_path, 'podspec.yaml'))
podspec = yaml.safe_load(open(podspec_path, encoding='utf-8'))
default_locale = podspec.get('localization', {}).get('default_locale', 'en')
www_root = os.path.abspath(os.path.join(pod_root_path, 'build')) + podspec.get('root', '/')
pod_root = podspec.get('root', '/')
locales = podspec.get('localization', {}).get('locales', [])

redirect_config = RedirectMiddleware.get_config()
trailing_slash_behavior = redirect_config.get('settings', {}).get('trailing_slash_behavior', 'add')
rewrite_content = redirect_config.get('settings', {}).get('rewrite_localized_content', True)
custom_404_page = redirect_config.get('settings', {}).get('custom_404_page')

mimetypes.add_type('text/template', '.mustache')


class StaticHandler(webapp2.RequestHandler):
  """Abstract class to handle serving static files."""

  def get(self, path='', status_code=None):
    path = path.lstrip('/')
    path = os.path.join(pod_root_path, 'build', path)

    if os.path.isdir(path):
      path = path.rstrip('/') + '/index.html'

    logging.info('Serving -> {}'.format(path))

    if not os.path.isfile(path):
      if custom_404_page:
        return self.get(custom_404_page, status_code=404)
      else:
        webapp2.abort(404)

    if status_code is not None:
      self.response.set_status(status_code)

    fp = open(path, 'rb')
    fd = os.open(path, os.O_RDWR|os.O_CREAT)
    info = os.fstat(fd)
    etag = '"{}{}{}"'.format(info.st_mtime, info.st_size, info.st_ino)
    request_etag = self.request.headers.get('If-None-Match')
    if etag == request_etag:
        self.response.status = 304
        return
    self.response.headers['ETag'] = etag
    self.response.headers['Content-Type'] = mimetypes.guess_type(path)[0] or 'text/plain'

    # Bypass the subclass's `write` method due to Python 3 incompatibility.
    # https://github.com/GoogleCloudPlatform/webapp2/issues/146
    super(webapp2.Response, self.response).write(fp.read())

    fp.close()
    os.close(fd)


class TrailingSlashRedirect(object):

    def __init__(self, app):
        self.app = app

    def redirect(self, environ, start_response, path):
      query_string = environ.get('QUERY_STRING', '')
      if query_string:
        destination = path + '?' + query_string
      else:
        destination = path
      status = '302 Found'
      response_headers = [('Location', destination)]
      start_response(status, response_headers)
      return []

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        base, ext = os.path.splitext(os.path.basename(path))

        # /index.html -> / redirect.
        if trailing_slash_behavior in ['remove', 'add']:
          if path.endswith('/index.html'):
              if trailing_slash_behavior == 'remove':
                path = path[:-11]
              elif trailing_slash_behavior == 'add':
                path = path[:-10]
              return self.redirect(environ, start_response, path)

        # Strip trailing slashes.
        # /foo/ -> /foo redirect.
        if trailing_slash_behavior == 'remove':
          if path.endswith('/') and len(path) > 1:
              path = path[:-1]
              return self.redirect(environ, start_response, path)

        # Enforce trailing slashes (default).
        # /foo -> /foo/ redirect.
        if trailing_slash_behavior == 'add':
          if base and not ext:
              path = '{}/'.format(path)
              return self.redirect(environ, start_response, path)

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
