from django.shortcuts import render_to_response
from django.http import HttpResponse
import json

import printqueue

def GetBaseQueueName(name):
  for x in ['duplex', 'simplex']:
    if '-%s' % x in name:
      name = name.replace('-%s' % x, '')
  return name

def Index(self):
  return render_to_response('printindex.html', {})

def QueueView(self, name):
  name = GetBaseQueueName(name)
  p = printqueue.PrintQueue(name)
  return render_to_response('queueview.html', {'queuename':name, 'queue':p})


def JSONQueueView(self, name):
  name = GetBaseQueueName(name)
  p = printqueue.PrintQueue(name)
  return HttpResponse(json.dumps(p.GetPublishedDict()),
                      mimetype='application/json')


