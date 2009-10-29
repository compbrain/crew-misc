#!/usr/bin/python
import json
import os
import sys
import web
from web import wsgiserver

import printqueue


## For Django Templating
from django.template.loader import render_to_string
from django.conf import settings
settings.configure(TEMPLATE_DIRS=(os.path.join(os.getcwd(), 'static'),))

urls = (
    '/', 'IndexHandler',
    '/queue/(.*)/', 'QueueView',
    '/jsonqueue/(.*)/', 'JSONQueueView',
)

def GetBaseQueueName(name):
  for x in ['duplex', 'simplex']:
    if '-%s' % x in name:
      name = name.replace('-%s' % x, '')
  return name

class IndexHandler:
  def GET(self):
    return render_to_string('printindex.html', {})

class QueueView:        
  def GET(self, name):
    name = GetBaseQueueName(name)
    p = printqueue.PrintQueue(name)
    return render_to_string('queueview.html', {'queuename':name, 'queue':p})


class JSONQueueView:
  def GET(self, name):
    name = GetBaseQueueName(name)
    p = printqueue.PrintQueue(name)
    return json.dumps(p.GetPublishedDict())


def apprunner(args=sys.argv):
  web.webapi.config.debug = False
  app = web.application(urls, globals()).wsgifunc()
  s = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 9090), app,
                                    server_name='cs4500.server')
  s.start()


if __name__ == "__main__":
    app.run()

