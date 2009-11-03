#!/usr/bin/python
"""Interface to CUPS Print Queues.

The two classes here contain logic for getting the state of print queues and
the jobs those queues contain. Focus is on getting a list of jobs at the head
of the queue and reporting on their status and ultimate endpoints.
"""

__author__ = 'Will Nowak <wan@ccs.neu.edu>'

import cgi
import cups
import cupsext
import json
import memcache
import optparse
import os
import time

MEMCACHE_HOST = None


class Job(object):
  """Represents the state of a print job."""

  STATUSMAP = {8:'aborted', 7:'canceled', 6:'stopped', 5:'processing',
               3:'pending', 4:'held', 9:'completed'}

  def __init__(self, dest, id, size, state, title, user, cupsinstance=None):
    """Initialize a Job object.

    Args:
       dest: (string) queue the job came from
       id: (int) job id number
       size: (int) job size in bytes
       state: (int) job state (one of the keys in STATUSMAP)
       title: (string) job title
       user: (string) job owner
       cupsinstance: (cups.Connection) cups connection object instance
    """
    self.dest = dest
    self.id = int(id)
    self.size = size
    self.state = state
    self.title = title
    self.user = user
    self.cups = cupsinstance
    self.cupsattributes = None
    self.memcache = None
    if not self.cups:
      self.cups = cups.Connection()

  def GetDict(self):
    """Get a dictionary representing this job for JSON conversion."""
    return {'id':self.id,
            'state':self.GetStatusText(),
            'physicaldest':self.GetOutputPrinterName(),
            'title':cgi.escape(self.GetRealTitle()), 
            'owner':cgi.escape(self.user),
            'finisher':self.dest,
            'source':self.GetJobSource(),
           }

  def __str__(self):
    """Get a string representing this job."""
    return ('%d = %s [%s] %s by %s is %s'
            % (self.id, self.GetOutputPrinterName(), self.GetFinisher(),
               self.GetRealTitle(), self.user, self.GetStatusText()))

  def __repr__(self):
    """Provide a representation of this job."""
    return str(self)

  def __cmp__(self, other):
    """Compare this job to another by comparing ID numbers."""
    return cmp(self.id, other.id)
  
  def MemcacheInterface(self):
    if MEMCACHE_HOST and not self.memcache:
      self.memcache = memcache.Client([MEMCACHE_HOST], debug=0)
    return self.memcache

  def CachedGetCUPSAttributes(self):
    """Try and get cups attributes from cache."""
    key = 'cups-job-attrs-%d' % self.id
    mc = self.MemcacheInterface()
    if mc and mc.get(key):
      self.cupsattributes = mc.get(key)
    else:
      self.cupsattributes = self.cups.getJobAttributes(self.id)
      if mc and self.IsComplete():
        mc.set(key, self.cupsattributes)
    return self.cupsattributes

  def GetCUPSAttributes(self):
    """Fetch cups job attributes for this job from the cups server."""
    if not self.cupsattributes:
      self.cupsattributes = self.CachedGetCUPSAttributes()
    return self.cupsattributes

  def GetPhysicalDest(self, given=None):
    """Get the queue name without its finisher component.

    Args:
       given: (string) queue name, if None, then self.dest is used.

    Returns:
       If queuename was 'hanna-duplex', 'hanna' would be returned.
    """
    if given is None:
      given = self.dest
    if self.GetFinisher() is not 'plain':
      given = given.replace('-%s' % self.GetFinisher(), '')
    return given

  def GetActualDestination(self):
    """Try and get the name of the endpoint print queue for this job."""
    attrs = self.GetCUPSAttributes() #['job-actual-printer-uri']
    if attrs and 'job-actual-printer-uri' in attrs:
      uri = attrs['job-actual-printer-uri']
    else:
      uri = self.dest
    return self.GetPhysicalDest(os.path.basename(uri))

  #XXX: Why do I have this here anymore?
  def GetOutputPrinterName(self):
    """Get the name of the printer that this job should come out of."""
    return self.GetPhysicalDest(self.GetActualDestination())

  def IsWindowsJob(self):
    """Determine if this job came from SAMBA or not."""
    return 'smbprn' in self.title

  def GetJobSource(self):
    """Get a string indicating the source of this job. (windows or not)"""
    if self.IsWindowsJob():
      return 'samba'
    else:
      return 'other'

  def GetRealTitle(self, obfuscate=True, truncatecount=14):
    """Get a string representing the title of this job.

    Args:
       obfuscate: (boolean) If True, truncate the title of this job
       truncatecount: (int) Number of characters to save during truncation
    Returns:
       job name = "Marry Had A Little Lamb"
       return value = "Marry Had A Li..."
    """
    if self.IsWindowsJob():
      t = self.title.split(' ', 1)[1]
    else:
      t = self.title
    if len(t) > truncatecount and obfuscate:
      return t[:truncatecount] + '...'
    else:
      return t

  def IsComplete(self):
    """Get a boolean determination if this job is done processing."""
    return self.GetStatusText() in ['aborted', 'canceled', 'completed']

  def GetStatusText(self):
    """Get a string representing the status of this job."""
    return self.STATUSMAP[self.state]

  def GetFinisher(self):
    """Get a string representing the finisher type in this jobs queue.

    Returns:
      simplex, duplex, or plain [for queues] (dali-dimplex, dali-duplex, dali)
    """
    for x in ['simplex', 'duplex']:
      if x in self.dest:
        return x
    return 'plain'

  @classmethod
  def GetFromCUPS(cls, cj, cups=None):
    """Get a Job instance from a cups job.
    
    Args:
       cj: (cupsext.Job object) job to clone
       cups: (cups.Connection) cups connection for metadata lookup
    """
    return cls(cj.dest, cj.id, cj.size, cj.state, cj.title, cj.user,
               cupsinstance=cups)

  @classmethod
  def GetJobs(cls, completed=False, cups=None):
    """Get a list of jobs for the cups server.
    
    Args:
       completed: (boolean) True = Get completed jobs, False = Get pending jobs
       cups: (cups.Connection) cups connection for metadata lookup
    Returns:
       list of Job instances
    """
    return [cls.GetFromCUPS(x, cups=cups)
            for x in cupsext.getJobs(0, int(completed))]

  @classmethod
  def GetJobsForPrinter(cls, printer, cups=None, completed=False):
    """Get a list of jobs for the given queue on the cups server.
    
    Args:
       printer: (string) cups queue name (class or printer)
       cups: (cups.Connection) cups connection for metadata lookup
       completed: (boolean) True = Get completed jobs, False = Get pending jobs
    Returns:
       list of Job instances
    """
    return [job for job in cls.GetJobs(completed, cups=cups) 
            if job.GetPhysicalDest() == printer]


class PrintQueue(object):
  """Represent a CUPS print queue."""

  STATUSMAP = {1287:'busy', 3:'idle', 1290:'deactivated', 4:'processing',
               5:'stopped'}

  def __init__(self, name):
    """Create a PrintQueue instance.

    Args:
       name: (string) name of the CUPS print queue.
    """
    self.cups = None
    self.alljobs = []
    self.name = name
    self.queuenames = None
    self.GetJobsForPrinter()
    self.AddClassMembers()

  def CupsConnection(self):
    try:
      if not self.cups:
        self.cups = cups.Connection()
      return self.cups
    except:
      time.sleep(1)
      return self.CupsConnection()

  def AllQueueNames(self):
    if not self.queuenames:
      self.queuenames = [self.name]
      if self.name in self.CupsConnection().getClasses():
        self.queuenames += self.CupsConnection().getClasses()[self.name]
    return self.queuenames

  def AddClassMembers(self):
    for x in self.AllQueueNames():
      self.GetJobsForPrinter(x)

  def GetJobsForPrinter(self, printer=None):
    if not printer:
      printer = self.name
    self.alljobs += Job.GetJobsForPrinter(printer, cups=self.CupsConnection(),
                                          completed=True)
    self.alljobs += Job.GetJobsForPrinter(printer, cups=self.CupsConnection(),
                                          completed=False)
    self.alljobs.sort()
    self.alljobs.reverse()

  def PendingJobs(self):
    return [job for job in self.alljobs if not job.IsComplete()]

  def FinishedJobs(self):
    return [job for job in self.alljobs if job.IsComplete()]

  def GetPublishedJobs(self, completecount=10):
    l = self.PendingJobs() + self.FinishedJobs()[:completecount]
    l.sort()
    l.reverse()
    return l

  def GetPublishedDict(self, completecount):
    return [x.GetDict() for x in self.GetPublishedJobs(completecount)]

  def GetPublishedJSON(self, completecount=10):
    j = {'jobs':self.GetPublishedDict(completecount),
         'status':self.QueueStatus(),
        }
    return json.dumps(j)

  def QueueStatus(self):
    statuslist = []
    p = self.CupsConnection().getPrinters()
    for x in p:
      if x in self.AllQueueNames():
        statuslist.append({'name': x,
          'status':PrintQueue.STATUSMAP[p[x]['printer-state']]})
    return statuslist


def GetParser():
  parser = optparse.OptionParser()
  parser.add_option('-c', '--count', type='int', default=10, dest='count',
                    help='The number of jobs to print. Default=10')
  return parser

if __name__ == '__main__':
  import sys
  parser = GetParser()
  options, args = parser.parse_args()
  p = PrintQueue('102')
  sys.stdout.write('=== Jobs for %s ===\n' % p.name)
  for job in p.GetPublishedJobs(options.count):
    sys.stdout.write('%s\n' % job)
