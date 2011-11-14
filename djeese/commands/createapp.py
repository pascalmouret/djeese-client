from collections import defaultdict
from djeese.apps import AppConfiguration
from djeese.commands import BaseCommand
from djeese.utils import slugify, get_package_data
import re
import requests

class BaseValidator(object):
    def validate(self, value):
        if not self.check(value):
            print self.message % value
            return False
        return True
    
    def check(self, value):
        return True


class URLValidator(object):
    message = "Could not open %r."
    
    def check(self, value):
        return requests.get(value, timeout=5).status_code == 200


class RegexValidator(BaseValidator):
    def __init__(self, regex, message, *flags):
        self.regex = re.compile(regex, *flags)
        self.message = message
    
    def check(self, value):
        return self.regex.match(value)


class SlugValidator(RegexValidator):
    def __init__(self):
        super(SlugValidator, self).__init__(r'^[-\w]+$', "May only contain alphanumeric characters and dashes")


def ask(title, *validators, **kwargs):
    default = kwargs.get('default', None)
    required = kwargs.get('required', True)
    if default:
        message = '%s [%s]: ' % (title, default)
    else:
        message = '%s: ' % title
    value = raw_input(message)
    if not value and default or not required:
        return default
    for validator in validators:
        if not validator.validate(value):
            return ask(title, *validators)
    return value

def ask_boolean(title, default=None):
    if default is None:
        message = '%s [y/n]: ' % title
    elif default:
        message = '%s [Y/n]: ' % title
    else:
        message = '%s [y/N]: ' % title
    value = raw_input(message)
    if not value and default is not None:
        return default
    elif value in ['y', 'Y']:
        return True
    elif value in ['n', 'N']:
        return False
    print "Please enter either 'n' or 'y'"
    ask_boolean(title, default)

def ask_multi(title, minitems=0):
    pass

def contrib(config, section, key, method, *args, **kwargs):
    value = method(*args, **kwargs)
    print repr(value)
    config[section][key] = value
    return value

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
        contrib(config, 'app', 'url', ask, 'URL', default=data['url'])
        contrib(config, 'app', 'author', ask, 'Author', default=data['author'])
        contrib(config, 'app', 'author_email', ask, 'Author email', default=data['author_email'])
        contrib(config, 'app', 'maintainer', ask, 'Maintainer (you)', default=data['author'])
        contrib(config, 'app', 'installed_apps', ask_multi, "Installed apps", minitems=1)
        contrib(config, 'app', 'version', ask, 'Version', default=data['version'])
        contrib(config, 'app', 'description', ask, 'Description (short)', default=data['description'])
        contrib(config, 'app', 'license', ask, 'License', default=data['license'])
        contrib(config, 'app', 'license_text_url', ask, 'License Text (URL)', URLValidator(), default=data['license_text_url'])
        fname = '%s.ini' % packagename
        config.write(fname)
