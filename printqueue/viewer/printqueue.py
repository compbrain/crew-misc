#!/usr/bin/python
"""Interface to CUPS Print Queues.

The two classes here contain logic for getting the state of print queues and
the jobs those queues contain. Focus is on getting a list of jobs at the head
of the queue and reporting on their status and ultimate endpoints.
"""

__author__ = 'Will Nowak <wan@ccs.neu.edu>'

import os
import cups
import cupsext


class Job(object):
  """Represents the state of a print job."""

  STATUSMAP = {8:'aborted', 7:'canceled', 6:'stopped', 5:'processing',
               3:'pending', 4:'held', 9:'completed'}

  def __init__(self, dest, id, size, state, title, user, cups=None):
    """Initialize a Job object.

    Args:
       dest: (string) queue the job came from
       id: (int) job id number
       size: (int) job size in bytes
       state: (int) job state (one of the keys in STATUSMAP)
       title: (string) job title
       user: (string) job owner
       cups: (cups.Connection) cups connection object instance
    """
    self.dest = dest
    self.id = int(id)
    self.size = size
    self.state = state
    self.title = title
    self.user = user
    self.cups = cups
    self.cupsattributes = None
    if not self.cups:
      self.cups = cups.Connection()

  def GetDict(self):
    """Get a dictionary representing this job for JSON conversion."""
    return {'id':self.id,
            'state':self.GetStatusText(),
            'physicaldest':self.GetOutputPrinterName(),
            'title':self.GetRealTitle(), 
            'owner':self.user,
            'finisher':self.dest,
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

  def GetCUPSAttributes(self):
    """Fetch cups job attributes for this job from the cups server."""
    if not self.cupsattributes:
      self.cupsattributes = self.cups.getJobAttributes(self.id)
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
    try:
      uri = self.GetCUPSAttributes()['job-actual-printer-uri']
      return self.GetPhysicalDest(os.path.basename(uri))
    except:
      return self.dest

  #XXX: Why do I have this here anymore?
  def GetOutputPrinterName(self):
    """Get the name of the printer that this job should come out of."""
    return self.GetPhysicalDest(self.GetActualDestination())

  def IsWindowsJob(self):
    """Determine if this job came from SAMBA or not."""
    return 'smbprn' in self.title

  def GetJobSource(self):
    """Get a string indicating the source of this job. (windows or not)"""
    if self.IsWindowsJob(self):
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
    return cls(cj.dest, cj.id, cj.size, cj.state, cj.title, cj.user, cups=cups)

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

  def __init__(self, name):
    """Create a PrintQueue instance.

    Args:
       name: (string) name of the CUPS print queue.
    """
    self.cups = cups.Connection()
    self.alljobs = []
    self.name = name
    self.GetJobsForPrinter()
    self.AddClassMembers()

  def AddClassMembers(self):
    if self.name in self.cups.getClasses():
      for x in self.cups.getClasses()[self.name]:
        self.GetJobsForPrinter(x)

  def GetJobsForPrinter(self, printer=None):
    if not printer:
      printer = self.name
    self.alljobs += Job.GetJobsForPrinter(printer, cups=self.cups,
                                         completed=True)
    self.alljobs += Job.GetJobsForPrinter(printer, cups=self.cups,
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

  def GetPublishedDict(self, completecount=10):
    return [x.GetDict() for x in self.GetPublishedJobs(completecount)]


if __name__ == '__main__':
  p = PrintQueue('102')
  print '=== Jobs for %s ===' % p.name
  for job in p.GetPublishedJobs():
    print job
