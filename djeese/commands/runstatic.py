from __future__ import with_statement
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import ForkingMixIn
from djeese.commands import BaseCommand, CommandError
from djeese.printer import Printer
from optparse import make_option
from requests.structures import CaseInsensitiveDict
import cgi
import os
import requests
import urlparse


class StaticHandler(SimpleHTTPRequestHandler):
    """
    Proxies everything to StaticServer.proxied_to except for paths starting
    with '/static/' if those files exist in StaticServer.staticfolder, in which
    case it serves the local file.
    """
    def do_GET(self):
        # check if it's a /static/ request
        _, _, path, _, query, _ = urlparse.urlparse(self.path)
        params = cgi.parse_qs(query)
        if path == '/login/':
            return self.send_message("We are sorry, but login is not supported yet")
        if path.startswith('/static/'):
            shortpath = path[8:]
            # translate the filepath
            filepath = os.path.join(self.server.staticfolder, shortpath)
            # check if it's there
            if os.path.exists(filepath):
                return self.serve_file(filepath)
        return self.proxy(path, params=params)
    
    def send_message(self, message):
        self.send_response(200)
        self.send_header("Content-type", 'text/plain')
        self.send_header('Content-Length', len(message))
        self.end_headers()
        self.wfile.write(message)
    
    def serve_file(self, filepath):
        """
        Serve the file at `filepath`. Code mostly taken from SimpleHTTPServer.
        """
        ctype = self.guess_type(filepath)
        try:
            fobj = open(filepath, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(fobj.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        self.copyfile(fobj, self.wfile)
    
    def do_POST(self):
        """
        Post ALWAYS gets proxied
        """
        message = "We are sorry, but POST requests are currently not allowed"
        return self.send_message(message)
        
        
        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        
        data = {}
        files = {}

        # Echo back information about what was posted in the form
        for field in form.keys():
            field_item = form[field]
            if field_item.filename:
                # The field contains an uploaded file
                files[field] = field_item.file
            else:
                # Regular form value
                data[field] = field_item.value

        return self.proxy('post', data, files)
    
    def proxy(self, path, method='get', params=None, data=None, files=None):
        """
        Proxy to the remote site using requests (which is awesome)
        
        This is a tad inefficient and slow, but should work for reasonably
        sized requests.
        """
        # get scheme and netlocation from remote server
        scheme, netloc, _, _, _ = urlparse.urlsplit(self.server.proxied_to)
        # extract get params
        # add the path
        url = urlparse.urlunsplit((scheme, netloc, path, '', ''))
        requestheaders = CaseInsensitiveDict(self.headers)
        requestheaders['referer'] = self.server.last
        requestheaders['host'] = netloc
        self.server.last = url
        # get the response
        method = getattr(self.server.session, method)
        extra = {}
        if method == 'get':
            extra['allow_redirects'] = True
        response = method(url, params=params, data=data, files=files, headers=requestheaders, **extra)
        content = response.raw.read()
        length = len(content)
        self.send_response(response.status_code)
        response.headers['content-length'] = str(length)
        # kill transfer-encoding, this server doesn't support it
        if 'transfer-encoding' in response.headers:
            del response.headers['transfer-encoding']
        # for some reason, sometimes the 'content-encoding' is reported as 
        # 'gzip' but isn't, so the quickfix is to kill that header.
        # TODO: Make this not that magical
        if 'content-encoding' in response.headers:
            del response.headers['content-encoding']
        # proxy the headers we got from the initial request
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.end_headers()
        # send the content
        self.wfile.write(content)
        
    def log_message(self, format, *args):
        self.server.printer.info(format % args)


class StaticServer(ForkingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, proxied_to, staticfolder, printer):
        self.proxied_to = proxied_to
        self.staticfolder = staticfolder
        self.printer = printer
        self.session = requests.session()
        self.last = proxied_to
        HTTPServer.__init__(self, server_address, RequestHandlerClass)


class Command(BaseCommand):
    help = 'Serve staticfiles from a local folder.'
    option_list = BaseCommand.option_list + (
        make_option('-p', '--port', action='store', dest='port', default='8080',
            help='The port of the server', type=int,
        ),
    )
    

    def handle(self, url=None, staticfolder='static', **options):
        if not url:
            raise CommandError("You must provide the url to your website file as first argument")
        if not os.path.exists(staticfolder):
            raise CommandError("Static folder %r not found." % staticfolder)
        server_address = ('', int(options['port']))
        printer = Printer(int(options['verbosity']))
        print "Open http://localhost:%s in your browser" % options['port']
        print "Use ctrl+c to stop the server"
        httpd = StaticServer(server_address, StaticHandler, url, staticfolder, printer)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            printer.always("Server shut down")
