#!/usr/bin/python
import os
import json
import sys
import gflags
from datetime import datetime
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

###

FLAGS = gflags.FLAGS

gflags.DEFINE_string('server', '', 'The server name on which to respond in order to serve the json (\'\' denotes anything which reaches this machine)')
gflags.DEFINE_integer('port', 8099, 'The port on which to serve the json')

###


class UTHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(self.uptime()))
        return
    def uptime(self):
        with open("/proc/uptime") as ut:
            read = ut.read().split()
            uptime = {'uptime':float(read[0]), 'idle':float(read[1])}
        return uptime
        
def main(argv):
    try:
        argv = FLAGS(argv) # parse flags
    except gflags.FlagsError, e:
        print '%s\n Usage: %s [flags]\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)
    try:
        server = HTTPServer((FLAGS.server, FLAGS.port), UTHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

if __name__ == '__main__':
    main(sys.argv)
