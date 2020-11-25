import logging
import os
from http.cookies import SimpleCookie

REDIRECTED_COOKIE = 'Grow-Static-Server-Locale-Redirected'
LOCALE_RESPONSE_HEADER = 'Grow-Static-Server-Locale'
TERRITORY_RESPONSE_HEADER = 'Grow-Static-Server-Territory'

LANGUAGE_PARAM = 'Grow-Static-Server-Language'
TERRITORY_PARAM = 'Grow-Static-Server-Territory'


class LocaleRedirectMiddleware(object):

    def __init__(self, app, www_root, pod_root, locales=None,
                 default_locale=None, rewrite_content=False):
        self.app = app
        self.www_root = www_root
        self.pod_root = pod_root
        self.default_locale = default_locale
        self.rewrite_content = rewrite_content
        if self.default_locale:
            self.default_locale = self.default_locale.lower()
        self.locales = locales or []
        self.locales = [locale.lower() for locale in self.locales]
        self.territories_to_identifiers = {}
        for locale in self.locales:
            territory = locale.split('_')[-1]
            territory = territory.lower()
            self.territories_to_identifiers[territory] = locale

    def set_redirected_cookie(self, response_headers):
        session_cookie = SimpleCookie()
        session_cookie[REDIRECTED_COOKIE] = '1'
        response_headers.extend(('set-cookie', morsel.OutputString())
                                for morsel in session_cookie.values())

    def redirect(self, locale_start_response, url):
        if url.endswith('/index.html'):
            url = url[:-11]
        url = '/{}'.format(url)
        status = '302 Found'
        response_headers = [('Location', url)]
        self.set_redirected_cookie(response_headers)
        locale_start_response(status, response_headers)
        return []

    def __call__(self, environ, start_response):
        # Extract territory from URL. If the URL is localized, return.
        # If it's not localized, check if a cookie is set.
        # If a cookie is set already, don't do anything and serve the app.
        # If no cookie, determine if there's a file on disk that matches
        # the locale, set the cookie, and redirect.
        url_path = environ['PATH_INFO'].lstrip('/')
        query_string = environ.get('QUERY_STRING', '')
        locale_part = url_path.split('/', 1)[0]
        locale_from_url = None

        session_cookie = SimpleCookie(os.getenv('HTTP_COOKIE', ''))
        has_redirected = REDIRECTED_COOKIE in session_cookie
        has_redirected = False

        # Do nothing if:
        #   - requesting a localized URL.
        #   - we've already redirected (determined by cookie).
        #   - "?ncr" (no country redirect) is in query string.
        if locale_part in self.locales or has_redirected or 'ncr' in query_string:
            locale_from_url = locale_part
            territory_from_url = locale_from_url.split('_')[-1]
            def matched_locale_start_response(status, headers, exc_info=None):
                headers.append((LOCALE_RESPONSE_HEADER, locale_part))
                if not has_redirected:
                    self.set_redirected_cookie(headers)
                return start_response(status, headers, exc_info)
            return self.app(environ, matched_locale_start_response)

        language_from_header = environ.get('HTTP_ACCEPT_LANGUAGE', '').split(',')[0]
        language_from_header = language_from_header.split('-')[0]
        territory_from_header = environ.get('HTTP_X_APPENGINE_COUNTRY', '')
        territory_from_header = territory_from_header.lower()
        locale_from_header = \
                self.territories_to_identifiers.get(territory_from_header, '')
        locale_from_header = locale_from_header.lower()

        # NOTE: Only language is considered currently, not the full locale
        # identifier.
        locale_from_header = language_from_header

        def locale_start_response(status, headers, exc_info=None):
            headers.append((LOCALE_RESPONSE_HEADER, locale_from_header))
            headers.append((TERRITORY_RESPONSE_HEADER, territory_from_header))
            return start_response(status, headers, exc_info)

        if not url_path:
            url_path = 'index.html'
        if url_path.endswith('/'):
            url_path += '/index.html'
        root_path_on_disk = os.path.join(self.www_root, url_path)
        localized_path_on_disk = None
        if locale_from_header:
            url_path = url_path.replace(self.pod_root.lstrip('/'), '')
            url_path = url_path.lstrip('/')
            localized_path_on_disk = os.path.join(
                    self.www_root, locale_from_header, url_path)
            localized_path_on_disk = localized_path_on_disk.replace('//', '/')

        # Rewrite the content with the localized content.
        if self.rewrite_content \
                and locale_from_header \
                and os.path.exists(localized_path_on_disk):
            f = open(localized_path_on_disk, 'rb')
            self.app(environ, locale_start_response)
            content = f.read()
            return [content]

        # Redirect the user if we have a localized file.
        if locale_from_header and os.path.exists(localized_path_on_disk):
            localized_path_on_disk = localized_path_on_disk.replace('./build/', './')
            url = localized_path_on_disk.replace('/index.html', '/')
            return self.redirect(locale_start_response, url)

        # If no file is found at the current location, and if we have a file at
        # a path corresponding to the default locale, redirect.
        if self.default_locale:
            default_localized_path_on_disk = os.path.join(
                    self.www_root, self.default_locale, url_path)
            if not os.path.exists(root_path_on_disk) \
                    and os.path.exists(default_localized_path_on_disk):
                url = os.path.join(self.default_locale, url_path)
                return self.redirect(locale_start_response, url)

        # Do nothing if user is in a country we don't have.
        return self.app(environ, locale_start_response)
