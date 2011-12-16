from __future__ import with_statement
from collections import defaultdict
from djeese.apps import AppConfiguration, VALID_TYPES
from djeese.commands import BaseCommand
from djeese.input_helpers import (RegexValidator, ask, SlugValidator, 
    ask_boolean, ask_multi, URLValidator, ask_choice, PathValidator)
from djeese.utils import slugify, get_package_data
import os

LICENSE_FILE_CANDIDATES = [
    'license',
    'license.txt',
    'LICENSE',
    'LICENSE.txt',
    'LICENSE.TXT',
]

def contrib(config, section, key, method, *args, **kwargs):
    """
    Wrapper to ask the user for input using `method` (passing `args` and
    `kwargs` to that method) and if a value is returned, set it in the `config`
    under `section` and `key`.
    """
    value = method(*args, **kwargs)
    if value:
        config[section][key] = value
    return value

def guess_path(name, modules):
    for module in modules:
        path = os.path.join(module, 'templates', name)
        if os.path.exists(path):
            return path
    return None

def guess_license_path():
    for candidate in LICENSE_FILE_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return


class Command(BaseCommand):
    help = 'Create a djeese apps.'

    def handle(self, **options):
        config = AppConfiguration(1)
        letterfirst = RegexValidator(r'^[a-zA-Z]', "Must start with a letter")
        name = contrib(config, 'app', 'name', ask, "Name", letterfirst)
        packagename = contrib(config, 'app', 'packagename', ask, 'Package name on PyPI', SlugValidator(), default=slugify(name))
        check_net = ask_boolean("Should we try to get additional information from djangopackages?", default=True)
        if check_net:
            data = get_package_data(packagename)
        else:
            data = defaultdict(lambda:None)
        modules = [p for p in os.listdir('.') if os.path.exists(os.path.join(p, '__init__.py'))]
        contrib(config, 'app', 'private', ask_boolean, "Private", default=False)
        contrib(config, 'app', 'url', ask, 'URL', default=data['url'])
        contrib(config, 'app', 'author', ask, 'Author', default=data['author'], required=False)
        contrib(config, 'app', 'author-url', ask, 'Author URL (optional)', default=data['author_url'], required=False)
        contrib(config, 'app', 'installed-apps', ask_multi, "Installed apps", minitems=1)
        contrib(config, 'app', 'version', ask, 'Version', default=data['version'])
        contrib(config, 'app', 'description', ask, 'Description (short)', default=data['description'])
        contrib(config, 'app', 'license', ask, 'License', default=data['license'])
        contrib(config, 'app', 'license-path', ask, 'Path to license file', PathValidator(), default=guess_license_path())
        contrib(config, 'app', 'translation-url', ask, 'URL to the translation page, eg transifex (optional)', URLValidator(), required=False)
        contrib(config, 'app', 'settings', ask_multi, 'Settings (optional)')
        contrib(config, 'app', 'plugins', ask_multi, 'Plugin (class) names (optional)')
        contrib(config, 'app', 'apphook', ask_multi, 'Apphook (class) names (optional)')
        for setting in config['app'].getlist('settings'):
            contrib(config, setting, 'name', ask, 'Name of the setting %r (Python)' % setting)
            contrib(config, setting, 'verbose-name', ask, 'Verbose name of the setting %r' % setting)
            contrib(config, setting, 'type', ask_choice, 'Type of the setting %r' % setting, choices=VALID_TYPES)
            contrib(config, setting, 'default', ask, 'Default value for setting %r (optional)' % setting, required=False)
            contrib(config, setting, 'required', ask_boolean, 'Is setting %r required' % setting, default=True)
            if config[setting].get('default', None):
                contrib(config, setting, 'editable', ask_boolean, 'Is setting %r editable' % setting, default=True)
        if ask_boolean("Does your application expose templates?", default=True) == 'true':
            while True:
                name = ask('Template path (eg %s/plugin.html)' % config['app']['packagename'])
                path = ask('Path to the source of the template', PathValidator(), default=guess_path(name, modules))
                config['templates'][name] = path
                if ask_boolean("Are there more templates?") == 'false':
                    break
        fname = '%s.ini' % packagename
        config.write(fname)
