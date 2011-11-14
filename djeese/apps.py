# -*- coding: utf-8 -*-
from ConfigParser import SafeConfigParser
from StringIO import StringIO
from djeese.printer import Printer
from djeese.utils import check_urls


VALID_TYPES = ['string', 'stringtuplelist', 'stringlist', 'boolean']
REQUIRED_APP_KEYS = ['name', 'author', 'author-email', 'packagename',
                     'installed-apps', 'description', 'license-text',
                     'license', 'url', 'version']
EXTRA_APP_KEYS = ['installation', 'settings']
REQUIRED_SETTINGS_KEYS = ['name', 'verbose-name', 'type']
EXTRA_SETTINGS_KEYS = ['default', 'required', 'editable']

def validate_app(config, printer):
    valid = True
    if 'app' not in config:
        printer.error("Section 'app' not found")
        valid = False
    else:
        if not validate_app_section(config, printer):
            valid = False
    if 'templates' in config:
        if not validate_templates_section(config, printer):
            valid = False
    settings = config['app'].getlist('settings')
    for setting in settings:
        if not validate_settings_section(config, printer, setting):
            valid = False
    if valid:
        printer.info("Configuration valid")
    else:
        printer.error("Configuration invalid")
    return valid

def validate_app_section(config, printer):
    valid = True
    printer.info("Required section 'app' found")
    app = config['app']
    for required in REQUIRED_APP_KEYS:
        if required not in app:
            printer.error("Option '%s' not found in 'app' section" % required)
            valid = False
        else:
            printer.info("Required option '%s' found in 'app' section" % required)
    return valid

def validate_templates_section(config, printer):
    valid = True
    templates = config['templates'].as_dict()
    reverse_templates = dict([(v,k) for k,v in templates.items()])
    responses = check_urls(templates.values())
    for url, success in responses:
        name = reverse_templates[url]
        if not success:
            printer.error("Could not load template %r from %r" % (name, url))
            valid = False
        else:
            printer.info("Successfully loaded %r from %r" % (name, url))
    return valid

def validate_settings_section(config, printer, setting):
    valid = True
    if setting not in config:
        printer.error("Could not find settings section %r" % setting)
        return False
    setting_config = config[setting]
    for required in ['verbose-name', 'name', 'type']:
        if required not in setting_config:
            printer.error("Could not find required option %r in settings section %r" % (required, setting))
            valid = False
    if 'type' in setting_config:
        typevalue = setting_config['type']
        if typevalue not in VALID_TYPES:
            valid_types = ', '.join(VALID_TYPES)
            printer.error("Setting %r type %r is not valid. Valid choices: %s" % (setting, typevalue, valid_types))
    printer.info("Settings section valid")
    return valid

class Section(object):
    def __init__(self, parser, section):
        self.parser = parser
        self.section = section
    
    def items(self):
        return self.parser.items(self.section)
        
    def as_dict(self):
        return dict(self.items())
    
    def get(self, item, default=None):
        if item in self:
            return self[item]
        return default
        
    def getlist(self, item, default=None):
        if item in self:
            return [line.strip() for line in self[item].splitlines() if line.strip()]
        if default:
            return default
        return []
    
    def getint(self, item, default=0):
        if item in self:
            return self.parser.getint(self.section, item)
        return default
    
    def getfloat(self, item, default=0.0):
        if item in self:
            return self.parser.getfloat(self.section, item)
        return default
    
    def getboolean(self, item, default=False):
        if item in self:
            return self.parser.getboolean(self.section, item)
        return default
    
    def __contains__(self, item):
        return self.parser.has_option(self.section, item)
        
    def __getitem__(self, item):
        return self.parser.get(self.section, item)
    
    def __setitem__(self, item, value):
        self.parser.set(self.section, item, value)
        
    def __delitem__(self, item):
        self.parser.remove_option(self.section, item)


class AppConfiguration(object):
    def __init__(self, verbosity=1):
        self.parser = SafeConfigParser()
        self.printer = Printer(verbosity)
        
    def __getitem__(self, item):
        if item not in self:
            self.parser.add_section(item)
        return Section(self.parser, item)
    
    def __contains__(self, item):
        return self.parser.has_section(item)
    
    def read_string(self, data):
        sio = StringIO(data)
        sio.seek(0)
        self.parser.readfp(sio)
    
    def read(self, filepath):
        self.parser.read(filepath)
    
    def write(self, filepath):
        if not self.validate():
            return False
        with open(filepath, 'w') as fobj:
            self.parser.write(fobj)
        return True
    
    def validate(self):
        return validate_app(self, self.printer)
