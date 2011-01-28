import socket
import re
import json
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from time import time

###

network = 'irc.ccs.neu.edu'
port=6667
nick='aldwin_'
channel='#dds-c'

jsonserver=''
jsonport=8090

CHATLEN = 25

###

msgr = re.compile(':(.+)!(.+)@.+ PRIVMSG ([^:]+) :(.+)$')
chats = []
tgo = True
irc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

class IRCHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'chats':chats, 'channel':channel,
                                     'nick':nick, 'network':network}))
        return

def MonitorIRC():
    print 'Connecting...'
    irc.connect((network,port))
    print 'Connected.'
    irc.recv(4096)
    print 'Sending nickname'
    irc.send('NICK %s\r\n' % nick)
    irc.send('USER %s Python Python :Aldwin\'s Evil Twin\r\n' % nick)
    print 'Joining channel'
    irc.send('JOIN %s\r\n' % channel)
    irc.send('PRIVMSG %s :Greetings!\r\n' % channel)
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
            if ch == nick:
                ch = 'Private Msg'
            if len(chats) >= CHATLEN:
                del chats[0]
            chats.append({'channel':ch, 'nick':user,
                          'msg':msg, 'time':curtime})
            print '(' + ch + ')' + ' <' + user + '> ' + msg

def CloseIRC():
    print 'Closing.'
    irc.send('PART %s\r\n' % channel)
    irc.send('QUIT\r\n')
    irc.close()

def main():
    global tgo
    try:
        t = Thread(target=MonitorIRC)
        t.start()
        server = HTTPServer((jsonserver,jsonport), IRCHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        tgo = False
        CloseIRC()

if __name__ == '__main__':
    main()
