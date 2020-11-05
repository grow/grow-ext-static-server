from . import routetrie
import logging
import os
import urllib
import webob
import yaml


class RedirectMiddleware(object):

  def __init__(self, app):
    self.app = app
    self.redirects = routetrie.RouteTrie()
    self.init_redirects()

  def __call__(self, environ, start_response):
    request = webob.Request(environ)
    try:
      response = self.handle_request(request)
    except Exception:
      logging.exception('middleware exception: ')
      response = self.handle_error(request)
    return response(environ, start_response)

  def _configure_redirects(self):
    pod_root_path = os.path.join(os.path.dirname(__file__), '..', '..')
    yaml_path = os.path.abspath(os.path.join(pod_root_path, 'redirects.yaml'))
    py_path = os.path.abspath(os.path.join(pod_root_path, 'redirects.py'))
    if os.path.exists(yaml_path):
      redirects = yaml.safe_load(open(yaml_path))
      return redirects
    elif os.path.exists(py_path):
      return {}
    else:
      return {}

  def handle_request(self, request):
    # Seeing a lot of requests for /%FF for some reason, which errors when
    # webob.Request tries to decode it. Redirect /%FF to /.
    path_info = urllib.parse.quote(os.environ.get('PATH_INFO', ''))
    if path_info.lower() == r'/%ff':
      return self.redirect('/')

    # Check for redirects in data/redirects.txt file.
    redirect_uri = self.get_redirect_url(request.path)
    if redirect_uri:
      # Preserve query string for relative paths.
      if redirect_uri.startswith('/') and request.query_string:
        if '?' in redirect_uri:
          parts = urlparse.urlparse(redirect_uri)
          params = urlparse.parse_qs(parts.query)
          params.update(urlparse.parse_qs(request.query_string))
          qsl = []
          for key, vals in params.items():
            for val in vals:
              qsl.append((key, val))
          redirect_uri = '{}?{}'.format(parts.path, urllib.urlencode(qsl))
        else:
          redirect_uri = '{}?{}'.format(redirect_uri, request.query_string)

      logging.info('redirecting from %s to %s', request.path_qs, redirect_uri)
      return self.redirect(redirect_uri, code=302)

    # Render the WSGI response.
    return request.get_response(self.app)

  def handle_error(self, request):
    response = webob.Response()
    response.status = 500
    response.content_type = 'text/plain'
    response.text = 'An unexpected error has occurred.'
    return response

  def redirect(self, redirect_uri, code=302):
    """Returns a redirect response."""
    response = webob.Response()
    response.status = code
    response.location = redirect_uri
    return response

  def init_redirects(self):
    """Initializes the redirects trie."""
    for parts in self._configure_redirects():
      path, url = parts
      self.redirects.add(path, url)

  def get_redirect_url(self, path):
    """Looks up a redirect URL from the redirects trie."""
    url, params = self.redirects.get(path.lower())
    if not url:
      return None

    # Replace `$variable` placeholders in the URL.
    if '$' in url:
      for key, value in params.items():
        if key.startswith(':') or key.startswith('*'):
          url = url.replace('$' + key[1:], value)
    return url
