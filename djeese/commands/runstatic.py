from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import ForkingMixIn
from djeese.commands import BaseCommand, CommandError
import os
import requests
import urlparse


class StaticHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/static/'):
            path = self.path[8:]
            filepath = os.path.join(self.server.staticfolder, path)
            if os.path.exists(filepath):
                return self.serve_file(filepath)
        return self.proxy()
    
    def serve_file(self, filepath):
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
    
    def proxy(self):
        scheme, netloc, _, _, _ = urlparse.urlsplit(self.server.proxied_to)
        url = urlparse.urlunsplit((scheme, netloc, self.path, '', ''))
        response = requests.get(url)
        content = response.raw.read()
        length = len(content)
        self.send_response(response.status_code)
        if 'content-length' not in response.headers:
            response.headers['content-length'] = str(length)
        if 'transfer-encoding' in response.headers:
            del response.headers['transfer-encoding']
        if 'content-encoding' in response.headers:
            del response.headers['content-encoding']
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)


class StaticServer(ForkingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, proxied_to, staticfolder):
        self.proxied_to = proxied_to
        self.staticfolder = staticfolder
        HTTPServer.__init__(self, server_address, RequestHandlerClass)

        
class Command(BaseCommand):
    help = 'Serve staticfiles from a local folder.'

    def handle(self, url=None, staticfolder='static', **options):
        if not url:
            raise CommandError("You must provide the url to your website file as first argument")
        if not os.path.exists(staticfolder):
            raise CommandError("Static folder %r not found." % staticfolder)
        server_address = ('', 8080)
        httpd = StaticServer(server_address, StaticHandler, url, staticfolder)
        httpd.serve_forever()
