from djeese.input_helpers import ask, ask_password, ask_boolean
from djeese.printer import Printer
from optparse import make_option, OptionParser
import djeese
import os
import re
import sys
import urlparse

AUTH_FILE = os.path.join(os.path.expanduser('~'), '.djeese')
LOGIN_PATH = '/api/v1/login/'

class CommandError(Exception):
    """
    Exception class indicating a problem while executing a management
    command.

    If this exception is raised during the execution of a management
    command, it will be caught and turned into a nicely-printed error
    message to the appropriate output stream (i.e., stderr); as a
    result, raising this exception (with a sensible description of the
    error) is the preferred way to indicate that something has gone
    wrong in the execution of a command.

    """
    pass


class BaseCommand(object):
    option_list = (
        make_option('-v', '--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2', '3'],
            help='Verbosity level; 0=no output, 1=minimal output, 2=extra output, 3=all output'
        ),
    )
    help = ''
    args = ''
    
    def get_absolute_url(self, path):
        host = os.environ.get('DJEESE_HOST', 'https://control.djeese.com')
        scheme, netloc, _, query, fragment = urlparse.urlsplit(host)
        return urlparse.urlunsplit((scheme, netloc, path, query, fragment))
    
    def get_auth(self, noinput=False):
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
            if noinput or ask_boolean("Save login data?", default=True) == 'true':
                fobj = open(AUTH_FILE, 'w')
                try:
                    data = fobj.write(u'%s:%s' % (username, password))
                finally:
                    fobj.close()
        return username, password
    
    def usage(self, subcommand):
        """
        Return a brief description of how to use this command, by
        default from the attribute ``self.help``.

        """
        usage = '%%prog %s [options] %s' % (subcommand, self.args)
        if self.help:
            return '%s\n\n%s' % (usage, self.help)
        else:
            return usage
    
    def create_parser(self, prog_name, subcommand):
        """
        Create and return the ``OptionParser`` which will be used to
        parse the arguments to this command.

        """
        return OptionParser(prog=prog_name,
                            usage=self.usage(subcommand),
                            version=djeese.__version__,
                            option_list=self.option_list)

    def print_help(self, prog_name, subcommand):
        """
        Print the help message for this command, derived from
        ``self.usage()``.

        """
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()
    
    def run_from_argv(self, argv):
        """
        Given arguments, run this command.
        """
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        self.printer = Printer(int(options.verbosity))
        try:
            self.handle(*args, **options.__dict__)
        except CommandError, e:
            sys.stderr.write('%s\n' % e)
            sys.exit(1)
    
    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.

        """
        raise NotImplementedError()
