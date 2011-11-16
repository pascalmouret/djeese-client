# -*- coding: utf-8 -*-
from collections import defaultdict
import re
import requests
import unicodedata
import urlparse
import xmlrpclib
try:
    import json
except ImportError:
    import simplejson as json
try:
    from requests import async
except RuntimeError:
    class dummy_async(object):
        def get(self, url, **kwargs):
            return requests.get(url, **kwargs)
        
        def map(self, rs):
            return rs
    async = dummy_async()


LICENSE_FILE_CANDIDATES = [
    'license',
    'license.txt',
    'LICENSE',
    'LICENSE.txt',
    'LICENSE.TXT',
]

PYPI_KEYS = [
    'author',
    'author_email',
    'license',
    'version',
]

DJANGOPACKAGES_KEYS = [
    'repo_description',
]

def check_urls(urls, timeout=5):
    """
    Checks a list of URLs (asynchronously if possible)
    """
    rs = [async.get(url, timeout=5) for url in urls]
    return [(response.url, 200 <= response.status_code < 300) for response in async.map(rs)]

def _check_url(url):
    """
    Checks a single URL
    """
    return requests.get(url, timeout=5).status_code == 200

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    
    Slightly adapted from django.template.default_filters.slugify
    """
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

def _transform_pypi(data):
    """
    Transform the data from PyPI into the data we want.
    """
    return dict([(key, value) for key, value in data.items() if value != "UNKNOWN" and key in PYPI_KEYS])

def get_pypi_data(slug):
    """
    Download and process data on PyPI for an app with given slug, if available.
    If not available, returns empty dictionary.
    """
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    try:
        releases = client.package_releases(slug)
    except OSError:
        return {}
    if not releases:
        return {}
    release = releases[0]
    data = client.release_data(slug, release)
    return _transform_pypi(data)

def _find_license_url_bitbucket(scheme, netloc, path, tag):
    """
    Try to find the URL to the license text on bitbucket given a bitbucket
    repository URL (urlsplitted) and a version (tag).
    """
    for candidate in LICENSE_FILE_CANDIDATES:
        newpath = '%sraw/%s/%s' % (path, tag, candidate)
        url = urlparse.urlunsplit((scheme, netloc, newpath, '', ''))
        if _check_url(url):
            return url
    return None

def _find_license_url_github(scheme, netloc, path, tag):
    """
    Try to find the URL to the license text on github given a github
    repository URL (urlsplitted) and a version (tag).
    """
    for candidate in LICENSE_FILE_CANDIDATES:
        newpath = '%s/%s/%s' % (path, tag, candidate)
        newnetloc = 'raw.%s' % netloc
        url = urlparse.urlunsplit((scheme, newnetloc, newpath, '', ''))
        if _check_url(url):
            return url
    return None

def _find_license_url(repourl, version):
    """
    Try to find the URL to the license text either on github or bitbucket.
    """
    scheme, netloc, path, _, _ = urlparse.urlsplit(repourl)
    if netloc == 'github.com':
        return _find_license_url_github(scheme, netloc, path, version)
    elif netloc == 'bitbucket.org':
        return _find_license_url_bitbucket(scheme, netloc, path, version)
    else:
        return None
    
def _find_author_url(repourl):
    """
    Try to find the Author URL if the URL is on github or bitbucket.
    """
    scheme, netloc, path, _, _ = urlparse.urlsplit(repourl)
    if netloc in ['github.com', 'bitbucket.org']:
        newpath = '/'.join(path.split('/')[:2])
        return urlparse.urlunsplit((scheme, netloc, newpath, '', ''))
    else:
        return None

def _transform_djangopackages(data):
    """
    Process djangopackages data. 
    """
    url = data.get('repo_url', None)
    version = data.get('pypi_version', None)
    data = dict([(key, value) for key, value in data.items() if key in DJANGOPACKAGES_KEYS])
    data['license_text_url'] = None
    if url and version:
        license_text_url = _find_license_url(url, version)
        if license_text_url:
            data['license_text_url'] = license_text_url
    data['description'] = data.pop('repo_description', None)
    data['url'] = url
    data['author_url'] = _find_author_url(url)
    return data

def get_djangopackages_data(slug):
    """
    Download and process data from djangopackages using their API.
    """
    url = 'http://djangopackages.com/api/v1/package/%s/' % slug
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        return {'description': None}
    data = json.loads(response.content)
    return _transform_djangopackages(data)

def get_package_data(slug):
    """
    Get package data from Djangopackages and PyPI
    """
    data = defaultdict(lambda:None)
    data.update(get_pypi_data(slug))
    data.update(get_djangopackages_data(slug))
    return data
