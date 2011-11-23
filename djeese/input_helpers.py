# -*- coding: utf-8 -*-
import getpass
import re
import requests

class BaseValidator(object):
    """
    Base validator object.
    
    self.validate(value) calls self.check(value) and if not valid, prints
    self.message and return False. If valid, returns True
    """
    def validate(self, value):
        if not self.check(value):
            print self.message % value
            return False
        return True
    
    def check(self, value):
        return True


class URLValidator(BaseValidator):
    """
    Checks that a given URL is valid and can be accessed
    """
    message = "Could not open %r."
    
    def check(self, value):
        return requests.get(value, timeout=5).status_code == 200


class RegexValidator(BaseValidator):
    """
    Checks that a given value matches a regular expression
    """
    def __init__(self, regex, message, *flags):
        self.regex = re.compile(regex, *flags)
        self.message = message
    
    def check(self, value):
        return self.regex.match(value)


class SlugValidator(RegexValidator):
    """
    Checks that a given value is a slug (alphanumeric + underscores + dashes)
    """
    def __init__(self):
        super(SlugValidator, self).__init__(r'^[-\w]+$', "May only contain alphanumeric characters and dashes")


def ask(title, *validators, **kwargs):
    """
    Ask for a (single) value, validate using validators.
    
    If default is given, it will be returned if no input is given.
    
    If required is True, None is returned if no input is given.
    """
    default = kwargs.get('default', None)
    required = kwargs.get('required', True)
    if default:
        message = '%s [%s]: ' % (title, default)
    else:
        message = '%s: ' % title
    value = raw_input(message)
    if not value and default:
        return default
    if not value and not required:
        return None
    for validator in validators:
        if not validator.validate(value):
            return ask(title, *validators)
    return value

def ask_boolean(title, default=None):
    """
    Ask for a (single) boolean value.
    """
    if default is None:
        message = '%s [y/n]: ' % title
    elif default:
        message = '%s [Y/n]: ' % title
    else:
        message = '%s [y/N]: ' % title
    value = raw_input(message)
    if not value and default is not None:
        return 'true' if default else 'false'
    elif value in ['y', 'Y']:
        return 'true'
    elif value in ['n', 'N']:
        return 'false'
    print "Please enter either 'n' or 'y'"
    ask_boolean(title, default)

def ask_multi(title, minitems=0):
    """
    Ask for (at least) minitems values.
    """
    values = []
    while True:
        value = ask('%s (leave empty for next option)' % title, required=len(values) < minitems)
        if value:
            values.append(value)
        else:
            break
    # convert to string:
    if values:
        return '\n%s' % '    '.join(values)
    else:
        return None

def ask_choice(title, choices):
    """
    Make the user choose a single value from choices
    """
    choices_dict = dict([(str(index), choice) for index, choice in enumerate(choices)])
    print title
    for index, choice in enumerate(choices):
        print '(%s) %s' % (index, choice)
    value = ask("Please choose [0-%s]" % len(choices))
    while value not in choices_dict:
        print "Invalid choices"
        value = ask("Please choose [0-%s]" % len(choices))
    return choices_dict[value]

def ask_password(title):
    password = getpass.getpass(title)
    while not password:
        password = ask_password(title)
    return password
