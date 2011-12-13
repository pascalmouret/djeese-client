# -*- coding: utf-8 -*-
from StringIO import StringIO
from collections import defaultdict
import os
import re
import requests
import shutil
import subprocess
import tarfile
import tempfile
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
    data = dict([(key, value) for key, value in data.items() if key in DJANGOPACKAGES_KEYS])
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

def _bundle(workspace, setuppy, config):
    """
    Does the actual bundling for `bundle`.
    """
    fnull = open(os.devnull, 'w')
    try:
        subprocess.check_call(['python', setuppy, 'sdist', '-d', workspace], stdout=fnull, stderr=fnull)
    finally:
        fnull.close()
    eggfile = os.path.join(workspace, os.listdir(workspace)[0])
    bundle = StringIO()
    tarball = tarfile.open(fileobj=bundle, mode='w:gz')
    # add the egg
    tarball.add(eggfile, arcname='package.tar.gz')
    # add templates
    templates = config['templates'].as_dict()
    for arcname, fpath in templates.items():
        full_arcname = 'templates/%s' % arcname
        # backwards compatibility, check for URL:
        if fpath.startswith(('http://', 'https://')):
            response = requests.get(fpath)
            tarball.addfile(tarfile.TarInfo(full_arcname), response)
        else:
            tarball.add(fpath, arcname=full_arcname)
    # add license
    # backwards compatibility, check for old license-text option:
    if 'license-path' in config['app']:
        tarball.add(config['app']['license-path'], arcname='meta/LICENSE.txt')
    else:
        response = requests.get(config['app']['license-text'])
        tarball.addfile(tarfile.TarInfo('meta/LICENSE.txt'), response)
    # add the config
    configpath = os.path.join(workspace, 'config')
    with open(configpath, 'w') as fobj:
        config.write_file(fobj)
    tarball.add(configpath, 'meta/config.cfg')
    # close, seek, return
    tarball.close()
    bundle.seek(0)
    return bundle

def bundle_app(setuppy, config):
    """
    Bundles a setup.py and all other files required (templates/license) into
    a StringIO bundle (gzipped)
    """
    distdir = tempfile.mkdtemp(prefix='djeese')
    try:
        return _bundle(distdir, setuppy, config)
    finally:
        shutil.rmtree(distdir)
