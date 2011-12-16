# -*- coding: utf-8 -*-
from __future__ import with_statement
from djeese.commands import BaseCommand, CommandError, LOGIN_PATH
from djeese.input_helpers import ask_boolean
from djeese.printer import Printer
from optparse import make_option
import requests
import tarfile
import traceback

class Command(BaseCommand):
    help = 'Clone the static files from an website'
    option_list = BaseCommand.option_list + (
        make_option( '--noinput', action='store_true', dest='noinput', default=False,
            help='Do not ask for input. Always assume yes.'
        ),
    )

    def handle(self, website=None, outputdir='static', **options):
        if not options['noinput'] and ask_boolean("Are you sure? This will override all files in %s!" % outputdir, default=True) == 'false':
            return
        printer = Printer(int(options['verbosity']), logfile='djeese.log')
        if not website:
            raise CommandError("You must provide the name of the website from which you want to clone the static files as first argument")
        url = self.get_absolute_url('/api/v1/io/static/clone/')
        username, password = self.get_auth(options['noinput'])
        session = requests.session()
        login_url = self.get_absolute_url(LOGIN_PATH)
        response = session.post(login_url, {'username': username, 'password': password})
        if response.status_code != 204:
            printer.error("Login failed")
            return
        data = {'name': website}
        response = session.get(url, params=data)
        if response.status_code == 200:
            self.finish_clone(response, outputdir, printer)
        elif response.status_code == 400:
            self.handle_bad_request(response, printer)
            printer.always("Clone failed: Bad request")
        elif response.status_code == 403:
            printer.error("Authentication failed")
            printer.always("Clone failed")
        elif response.status_code == 502:
            printer.error("Temporarily unavailable")
            printer.always("Clone failed")
        else:
            printer.error("Unexpected response: %s" % response.status_code)
            printer.log_only(response.content)
            printer.always("Clone failed, check djeese.log for more details")
    
    def finish_clone(self, response, outputdir, printer):
        try:
            tarball = tarfile.open(mode='r|gz', fileobj=response.raw)
        except:
            printer.error("Response not a valid tar file.")
            printer.always("Clone failed")
            traceback.print_exc(printer.logfile)
            return
        tarball.extractall(outputdir)
        printer.info("Clone successful")
