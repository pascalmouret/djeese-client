# -*- coding: utf-8 -*-
from djeese.apps import AppConfiguration
from djeese.commands import BaseCommand, CommandError
from djeese.input_helpers import ask, ask_password, ask_boolean
from djeese.printer import Printer
import os
import requests
import shutil
import subprocess
import tempfile

TARGET_URL = 'https://control.djeese.com/api/v1/apps/upload/'
LOGIN_URL = 'https://control.djeese.com/api/v1/login/'

AUTH_FILE = os.path.join(os.path.expanduser('~'), '.djeese')

class Command(BaseCommand):
    help = 'Upload an app.'

    def handle(self, setupfile=None, appfile=None, **options):
        if not setupfile:
            raise CommandError("You must provide the path to your apps setup.py as first argument")
        if not appfile:
            raise CommandError("You must provide the path to your app file as first argument")
        if not os.path.exists(setupfile):
            raise CommandError("Could not find setup.py at %r" % setupfile)
        if not os.path.exists(appfile):
            raise CommandError("Could not find setup.py at %r" % appfile)
        username, password = self.get_auth()
        distdir = tempfile.mkdtemp(prefix='djeese')
        try:
            self.run(setupfile, appfile, distdir, username, password, **options)
        finally:
            shutil.rmtree(distdir)
    
    def get_auth(self):
        username, password = None, None
        if os.path.exists(AUTH_FILE):
            fobj = open(AUTH_FILE)
            try:
                data = fobj.read()
            finally:
                fobj.close()
            if data.count(':') == 1:
                username, password = [bit.strip() for bit in data.split(':')]
        if not (username and password):
            username = ask("Username")
            password = ask_password("Password:")
            if ask_boolean("Save login data?", default=True) == 'true':
                fobj = open(AUTH_FILE, 'w')
                try:
                    data = fobj.write(u'%s:%s' % (username, password))
                finally:
                    fobj.close()
        return username, password
                
    
    def run(self, setupfile, appfile, distdir, username, password, **options):
        fnull = open(os.devnull, 'w')
        try:
            subprocess.check_call(['python', setupfile, 'sdist', '-d', distdir], stdout=fnull)
        finally:
            fnull.close()
        eggfile = os.path.join(distdir, os.listdir(distdir)[0])
        config = AppConfiguration(int(options['verbosity']))
        config.read(appfile)
        config.validate()
        appname = config['app']['name']
        response = self.upload(appfile, appname, eggfile, username, password)
        printer = Printer(int(options['verbosity']))
        if response.status_code == 201:
            printer.always("Upload successful (created)")
        elif response.status_code == 204:
            printer.always("Upload successful (updated)")
        elif response.status_code == 400:
            printer.error(response.content)
            printer.always("Upload failed")
        elif response.status_code == 403:
            printer.error("Authentication failed")
            printer.always("Upload failed")
        elif response.status_code == 502:
            printer.error("Temporarily unavailable")
            printer.always("Upload failed")
        else:
            printer.error("Unexpected response: %s" % response.status_code)
            printer.error(response.content)
            printer.always("Upload failed")
        
    def upload(self, configfile, appname, eggfile, username, password):
        with open(configfile, 'r') as configfileobj:
            configdata = configfileobj.read()
        with open(eggfile, 'rb') as eggfileobj:
            files = {
                'egg': eggfileobj,
            }
            data = {
                'config': configdata,
                'app': appname,
            }
            session = requests.session()
            response = session.post(LOGIN_URL, {'username': username, 'password': password})
            if response.status_code != 204:
                return response 
            response = session.post(TARGET_URL, data=data, files=files)
            return response
