"""The mock internal website. Serves site/ on 127.0.0.1:8012 and nothing else.

Bound to loopback INSIDE the container, deliberately. Two consequences, and the
second one surprised us, so it is written down:

  1. Nothing is reachable from outside the container and nothing leaves the
     student's machine. This is the rule for every lab in the course.
  2. A `docker run -p` flag would therefore publish a host port that forwards to
     a listener refusing every connection - measured with a control on
     2026-09-19. So this lab publishes no port and promises no browser view. You
     read the pages the way the assistant does, with curl, which is also the
     only view that shows you a payload a browser is designed to hide.

/etc/hosts maps news.acme.com to 127.0.0.1 so the URL looks like a real internal
site while resolving locally. That mapping is written by entrypoint.sh at run
time, not at build time: Docker rewrites /etc/hosts on container start.
"""
import http.server
import os
import socketserver

PORT = 8012
os.chdir("/labs/lab12/site")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Quiet) as httpd:
    httpd.serve_forever()
