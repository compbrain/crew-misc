#!/usr/bin/python
import os
import cups
import cupsext

class Job(object):
  STATUSMAP = {8:'aborted', 7:'canceled', 6:'stopped', 5:'processing',
               3:'pending', 4:'held', 9:'completed'}

  def __init__(self, dest, id, size, state, title, user, cups=None):
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
    return {'id':self.id,
            'state':self.GetStatusText(),
            'physicaldest':self.GetOutputPrinterName(),
            'title':self.GetRealTitle(), 
            'owner':self.user,
            'finisher':self.dest,
           }

  def __str__(self):
    return ('%d = %s [%s] %s by %s is %s'
            % (self.id, self.GetOutputPrinterName(), self.GetFinisher(),
               self.GetRealTitle(), self.user, self.GetStatusText()))

  def __repr__(self):
    return str(self)

  def __cmp__(self, other):
    return cmp(self.id, other.id)

  def GetCUPSAttributes(self):
    if not self.cupsattributes:
      self.cupsattributes = self.cups.getJobAttributes(self.id)
    return self.cupsattributes

  def GetActualDestination(self):
    try:
      uri = self.GetCUPSAttributes()['job-actual-printer-uri']
      return self.GetPhysicalDest(os.path.basename(uri))
    except:
      return self.dest

  def GetOutputPrinterName(self):
    return self.GetPhysicalDest(self.GetActualDestination())

  def IsWindowsJob(self):
    return 'smbprn' in self.title

  def GetJobSource(self):
    if self.IsWindowsJob(self):
      return 'samba'
    else:
      return 'other'

  def GetRealTitle(self, obfuscate=True, truncatecount=14):
    if self.IsWindowsJob():
      t = self.title.split(' ', 1)[1]
    else:
      t = self.title
    if len(t) > truncatecount and obfuscate:
      return t[:truncatecount] + '...'
    else:
      return t

  def IsComplete(self):
    return self.GetStatusText() in ['aborted', 'canceled', 'completed']

  def GetStatusText(self):
    return self.STATUSMAP[self.state]

  def GetFinisher(self):
    for x in ['simplex', 'duplex']:
      if x in self.dest:
        return x
    return 'plain'

  def GetPhysicalDest(self, given=None):
    if given is None:
      given = self.dest
    if self.GetFinisher() is not 'plain':
      given = given.replace('-%s' % self.GetFinisher(), '')
    return given

  @classmethod
  def GetFromCUPS(cls, cj, cups=None):
    """cj = cupsjob."""
    return cls(cj.dest, cj.id, cj.size, cj.state, cj.title, cj.user, cups=cups)

  @classmethod
  def GetJobs(cls, completed=False, cups=None):
    return [cls.GetFromCUPS(x, cups=cups)
            for x in cupsext.getJobs(0, int(completed))]

  @classmethod
  def GetJobsForPrinter(cls, printer, cups=None, completed=False):
    return [job for job in cls.GetJobs(completed, cups=cups) 
            if job.GetPhysicalDest() == printer]

class PrintQueue(object):
  def __init__(self, printer):
    self.cups = cups.Connection()
    self.alljobs = []
    self.printer = printer
    self.GetJobsForPrinter()
    self.AddClassMembers()

  def AddClassMembers(self):
    if self.printer in self.cups.getClasses():
      for x in self.cups.getClasses()[self.printer]:
        self.GetJobsForPrinter(x)

  def GetJobsForPrinter(self, printer=None):
    if not printer:
      printer = self.printer
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
  print '=== Jobs ==='
  for job in p.GetPublishedJobs():
    print job
