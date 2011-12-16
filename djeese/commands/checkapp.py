from __future__ import with_statement
from djeese.apps import AppConfiguration
from djeese.commands import BaseCommand, CommandError
import os
import sys

class Command(BaseCommand):
    help = 'Validate a djeese apps.'

    def handle(self, appfile=None, **options):
        if not appfile:
            raise CommandError("You must provide the path to your app file as first argument")
        if not os.path.exists(appfile):
            raise CommandError("App file %r not found." % appfile)
        appconfig = AppConfiguration(int(options['verbosity']))
        appconfig.read(appfile)
        if not appconfig.validate():
            sys.exit(1)
