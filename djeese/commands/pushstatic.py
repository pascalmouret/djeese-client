# -*- coding: utf-8 -*-
from StringIO import StringIO
from djeese import errorcodes
from djeese.commands import BaseCommand, CommandError, LOGIN_PATH
from djeese.input_helpers import ask_boolean
from djeese.printer import Printer
from optparse import make_option
import os
import re
import requests
import tarfile
try:
    from tarfile import bltn_open
except ImportError: # 2.5 compatiblity
    bltn_open = file 

FILENAME_BASIC_RE = re.compile(r'^[a-zA-Z]+[a-zA-Z0-9._-]*\.[a-zA-Z]{2,4}$')
ALLOWED_EXTENSIONS = [
    '.js',
    '.css',
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.htc',
]


def is_valid_file_name(name, printer):
    if not FILENAME_BASIC_RE.match(name):
        printer.always("File name %r is not a valid file name, ignoring..." % name)
        return False
    ext = os.path.splitext(name)[-1]
    if ext not in ALLOWED_EXTENSIONS:
        printer.always("File extension %r is not allowed, ignoring" % ext)
        return False
    return True



class TarfileBackport(tarfile.TarFile):
    def add(self, name, arcname=None, recursive=True, exclude=None, filter=None):
        """Add the file `name' to the archive. `name' may be any type of file
           (directory, fifo, symbolic link, etc.). If given, `arcname'
           specifies an alternative name for the file in the archive.
           Directories are added recursively by default. This can be avoided by
           setting `recursive' to False. `exclude' is a function that should
           return True for each filename to be excluded. `filter' is a function
           that expects a TarInfo object argument and returns the changed
           TarInfo object, if it returns None the TarInfo object will be
           excluded from the archive.
        """
        self._check("aw")

        if arcname is None:
            arcname = name

        # Exclude pathnames.
        if exclude is not None:
            import warnings
            warnings.warn("use the filter argument instead",
                    DeprecationWarning, 2)
            if exclude(name):
                self._dbg(2, "tarfile: Excluded %r" % name)
                return

        # Skip if somebody tries to archive the archive...
        if self.name is not None and os.path.abspath(name) == self.name:
            self._dbg(2, "tarfile: Skipped %r" % name)
            return

        self._dbg(1, name)

        # Create a TarInfo object from the file.
        tarinfo = self.gettarinfo(name, arcname)

        if tarinfo is None:
            self._dbg(1, "tarfile: Unsupported type %r" % name)
            return

        # Change or exclude the TarInfo object.
        if filter is not None:
            tarinfo = filter(tarinfo)
            if tarinfo is None:
                self._dbg(2, "tarfile: Excluded %r" % name)
                return

        # Append the tar header and data to the archive.
        if tarinfo.isreg():
            f = bltn_open(name, "rb")
            self.addfile(tarinfo, f)
            f.close()

        elif tarinfo.isdir():
            self.addfile(tarinfo)
            if recursive:
                for f in os.listdir(name):
                    self.add(os.path.join(name, f), os.path.join(arcname, f),
                            recursive, exclude, filter)

        else:
            self.addfile(tarinfo)


class Command(BaseCommand):
    help = 'Clone the static files from an website'
    option_list = BaseCommand.option_list + (
        make_option( '--noinput', action='store_true', dest='noinput', default=False,
            help='Do not ask for input. Always assume yes.'
        ),
    )

    def handle(self, website=None, sourcedir='static', **options):
        if not options['noinput'] and ask_boolean("Are you sure? This will override all files remotely!", default=True) == 'false':
            return
        printer = Printer(int(options['verbosity']), logfile='djeese.log')
        if not website:
            raise CommandError("You must provide the name of the website from which you want to push the static files as first argument")
        if not os.path.exists(sourcedir):
            raise CommandError("Source directory %r not found" % sourcedir)
        url = self.get_absolute_url('/api/v1/io/static/push/')
        username, password = self.get_auth(options['noinput'])
        session = requests.session()
        login_url = self.get_absolute_url(LOGIN_PATH)
        response = session.post(login_url, {'username': username, 'password': password})
        if response.status_code != 204:
            printer.error("Login failed")
            return
        data = {'name': website}
        files = {'static': self.build_tarball(sourcedir, printer)}
        response = session.post(url, data=data, files=files)
        if response.status_code == 204:
            printer.always("Sucess")
        elif response.status_code == 400:
            self.handle_bad_request(response, printer)
            printer.always("Push failed: Bad request")
        elif response.status_code == 403:
            printer.error("Authentication failed")
            printer.always("Push failed")
        elif response.status_code == 502:
            printer.error("Temporarily unavailable")
            printer.always("Push failed")
        else:
            printer.error("Unexpected response: %s" % response.status_code)
            printer.log_only(response.content)
            printer.always("Push failed, check djeese.log for more details")
    
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
        elif code == errorcodes.INVALID_WEBSITE:
            printer.error("Website with name %r not found" % meta)
        elif code == errorcodes.ACCESS_DENIED:
            printer.error("Access denied")
        elif code == errorcodes.ACCESS_DENIED:
            printer.error("Access denied")
        elif code == errorcodes.INVALID_FILENAME:
            printer.error("Filename %r is not allowed" % meta)
        else:
            printer.error("Unexpected error code: %s (%s)" % (code, meta))
        printer.info(response.content)
    
    def build_tarball(self, sourcedir, printer):
        buffer = StringIO()
        tarball = TarfileBackport.open(fileobj=buffer, mode='w:gz')
        def static_files_filter(tarinfo):
            if not tarinfo.isfile():
                return tarinfo
            if is_valid_file_name(os.path.basename(tarinfo.name), printer):
                return tarinfo
            return None
        tarball.add(sourcedir, filter=static_files_filter)
        tarball.close()
        buffer.seek(0)
        return buffer
    