#!/usr/bin/python
import socket
import re
import json
import sys
import gflags
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from time import time

###

FLAGS = gflags.FLAGS

gflags.DEFINE_string('network', 'irc.ccs.neu.edu', 'The IRC network to connect to')
gflags.DEFINE_integer('port', 6667, 'The port on which to connect to IRC')
gflags.DEFINE_string('nick', 'aldwin_', 'The nickname for the bot to use')
gflags.DEFINE_string('channel', '#dds-c', 'The IRC channel to monitor')
gflags.DEFINE_string('jsonserver', '', 'The server name on which respond in order to serve the json (\'\' denotes anything which reaches this machine)')
gflags.DEFINE_integer('jsonport', 8090, 'The port on which to serve the json')

CHATLEN = 25

###

msgr = re.compile(':(.+)!(.+)@.+ PRIVMSG ([^:]+) :(.+)$')
chats = []
tgo = True
irc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

class IRCHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Respond to any request with the json
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'chats':chats,
                                     'channel':FLAGS.channel,
                                     'nick':FLAGS.nick,
                                     'network':FLAGS.network}))
        return

def MonitorIRC():
    print 'Connecting...'
    irc.connect((FLAGS.network, FLAGS.port))
    print 'Connected.'
    irc.recv(4096)
    print 'Sending nickname'
    irc.send('NICK %s\r\n' % FLAGS.nick)
    irc.send('USER %s Python Python :Aldwin\'s Evil Twin\r\n' % FLAGS.nick)
    print 'Joining channel'
    irc.send('JOIN %s\r\n' % FLAGS.channel)
    irc.send('PRIVMSG %s :Greetings!\r\n' % FLAGS.channel)
    print 'All set.'
    while tgo:
        data = irc.recv(4096)
        if data.find('PING')!=-1:
            #keep-alive
            irc.send('PONG ' + data.split()[1] + '\r\n')
        elif data.find('PRIVMSG')!=-1:
            #message
            curtime = time()
            rdata = msgr.match(data)
            if not rdata:
                continue
            user = rdata.group(1)
            uname = rdata.group(2)
            ch = rdata.group(3)
            msg = rdata.group(4).replace('\r','').replace('\n','')
            if ch == FLAGS.nick:
                ch = 'Private Msg'
            if len(chats) >= CHATLEN:
                # remove the oldest message
                del chats[0]
            chats.append({'channel':ch, 'nick':user,
                          'msg':msg, 'time':curtime})
            print '(' + ch + ')' + ' <' + user + '> ' + msg

def CloseIRC():
    print 'Closing.'
    irc.send('PART %s\r\n' % FLAGS.channel)
    irc.send('QUIT\r\n')
    irc.close()

def main(argv):
    try:
      argv = FLAGS(argv)  # parse flags
    except gflags.FlagsError, e:
      print '%s\nUsage: %s [flags]\n%s' % (e, sys.argv[0], FLAGS)
      sys.exit(1)
    global tgo
    try:
        t = Thread(target=MonitorIRC)
        t.start()
        server = HTTPServer((FLAGS.jsonserver,FLAGS.jsonport), IRCHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        tgo = False
        CloseIRC()

if __name__ == '__main__':
    main(sys.argv)
