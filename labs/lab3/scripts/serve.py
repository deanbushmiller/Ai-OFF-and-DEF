"""The mock website. Serves site/ on 127.0.0.1:8003 and nothing else.

Bound to loopback deliberately. Nothing is reachable from outside the container,
and nothing leaves the student's machine. /etc/hosts maps news.acme.com to
127.0.0.1, so the URL looks like a real news site while resolving locally.
"""
import http.server
import os
import socketserver

PORT = 8003
os.chdir("/labs/lab3/site")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Quiet) as httpd:
    httpd.serve_forever()
