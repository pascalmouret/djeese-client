# -*- coding: utf-8 -*-
from __future__ import with_statement
from djeese import errorcodes
from djeese.apps import AppConfiguration
from djeese.commands import BaseCommand, CommandError, LOGIN_PATH
from djeese.printer import Printer
from djeese.utils import bundle_app
from optparse import make_option
import os
import requests


UPLOAD_PATH = '/api/v1/apps/upload-bundle/'


class Command(BaseCommand):
    help = 'Upload an app.'
    option_list = BaseCommand.option_list + (
        make_option( '--noinput', action='store_true', dest='noinput', default=False,
            help='Do not ask for input. Always assume yes.'
        ),
    )

    def handle(self, setupfile=None, appfile=None, **options):
        if not setupfile:
            raise CommandError("You must provide the path to your apps setup.py as first argument")
        if not appfile:
            raise CommandError("You must provide the path to your app file as first argument")
        if not os.path.exists(setupfile):
            raise CommandError("Could not find setup.py at %r" % setupfile)
        if not os.path.exists(appfile):
            raise CommandError("Could not find setup.py at %r" % appfile)
        username, password = self.get_auth(options['noinput'])
        self.run(setupfile, appfile, username, password, **options)

    def run(self, setupfile, appfile, username, password, **options):
        printer = Printer(int(options['verbosity']), logfile='djeese.log')
        config = AppConfiguration(printer=printer)
        config.read(appfile)
        bundle = bundle_app(setupfile, config) 
        appname = config['app']['name']
        response = self.upload(appname, bundle, username, password)
        if response.status_code == 201:
            printer.always("Upload successful (created)")
        elif response.status_code == 204:
            printer.always("Upload successful (updated)")
        elif response.status_code == 400:
            self.handle_bad_request(response, printer)
            printer.always("Upload failed")
        elif response.status_code == 403:
            printer.error("Authentication failed")
            printer.always("Upload failed")
        elif response.status_code == 502:
            printer.error("Temporarily unavailable")
            printer.always("Upload failed")
        else:
            printer.error("Unexpected response: %s" % response.status_code)
            printer.log_only(response.content)
            printer.always("Upload failed, check djeese.log for more details")
    
    def handle_bad_request(self, response, printer):
        code = int(response.headers.get('X-DJEESE-ERROR-CODE', 0))
        meta = response.headers.get('X-DJEESE-ERROR-META', '')
        if code == errorcodes.UNKNOWN:
            if meta:
                printer.error('Unknown error: %s' % meta)
            else:
                printer.error('Unknown error')
        elif code == errorcodes.INVALID_TAR:
            printer.error("Invalid tar file supplied")
        elif code == errorcodes.ACCESS_DENIED:
            printer.error("Access denied")
        elif code == errorcodes.NO_PACKAGE:
            printer.error("Package file missing from upload")
        elif code == errorcodes.NO_LICENSE:
            printer.error("License file missing from upload")
        elif code == errorcodes.NO_CONFIG:
            printer.error("Configuration missing from upload")
        elif code == errorcodes.INVALID_CONFIG:
            printer.error("Invalid configuration")
        elif code == errorcodes.MISSING_TEMPLATE:
            printer.error("Missing template %r" % meta)
        elif code == errorcodes.NAME_MISMATCH:
            printer.error("Supplied name does not match name in configuration")
        elif code == errorcodes.VERSION_TOO_LOW:
            server, supplied = meta.split(',')
            printer.error("Supplied version (%s) is not newer than version on server (%s)" % (supplied, server))
        elif code == errorcodes.PRIVATE_APP_QUOTA:
            printer.error("Cannot add new private app, please upgrade your plan")
        else:
            printer.error("Unexpected error code: %s (%s)" % (code, meta))
        printer.info(response.content)

    def upload(self, appname, bundle, username, password):
        files = {
            'bundle': bundle,
        }
        data = {
            'app': appname,
        }
        session = requests.session()
        login_url = self.get_absolute_url(LOGIN_PATH)
        response = session.post(login_url, {'username': username, 'password': password})
        if response.status_code != 204:
            return response
        target_url = self.get_absolute_url(UPLOAD_PATH)
        response = session.post(target_url, data=data, files=files)
        return response
