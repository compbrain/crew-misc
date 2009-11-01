from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.conf import settings

import printqueue
printqueue.MEMCACHE_HOST = settings.MEMCACHE_HOST

def GetBaseQueueName(name):
  """
  >>> GetBaseQueueName('reiniger-duplex')
  'reiniger'
  >>> GetBaseQueueName('reiniger-simplex')
  'reiniger'
  >>> GetBaseQueueName('reiniger')
  'reiniger'
  """
  return name.split('-')[0]


def QueueView(self, name, template_name='viewer/queueview.html'):
  name = GetBaseQueueName(name)
  p = printqueue.PrintQueue(name)
  return render_to_response(template_name, {'queuename':name, 'queue':p})


def JSONQueueView(self, name):
  name = GetBaseQueueName(name)
  p = printqueue.PrintQueue(name)
  return HttpResponse(p.GetPublishedJSON(), mimetype='application/json')
