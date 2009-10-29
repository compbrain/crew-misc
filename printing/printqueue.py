#!/usr/bin/python
import cupsext

class Job(object):
  STATUSMAP = {8:'aborted', 7:'canceled', 6:'stopped', 5:'processing',
               3:'pending', 4:'held', 9:'completed'}

  def __init__(self, dest, id, size, state, title, user):
    self.dest = dest
    self.physicaldest = None
    self.GetPhysicalDest()
    self.id = int(id)
    self.size = size
    self.state = state
    self.title = title
    self.user = user

  def __str__(self):
    return ('%s [%s] %s by %s is %s'
            % (self.dest, self.GetPhysicalDest(), self.GetRealTitle(),
               self.user, self.GetStatusText()))

  def __repr__(self):
    return str(self)

  def __cmp__(self, other):
    return cmp(self.id, other.id)

  def IsWindowsJob(self):
    return 'smbprn' in self.title

  def GetJobSource(self):
    if self.IsWindowsJob(self):
      return 'samba'
    else:
      return 'other'

  def GetRealTitle(self):
    if self.IsWindowsJob():
      return self.title.split(' ', 1)[1]
    else:
      return self.title

  def IsComplete(self):
    return self.GetStatusText() in ['aborted', 'canceled', 'completed']

  def GetStatusText(self):
    return self.STATUSMAP[self.state]

  def GetPhysicalDest(self):
    if self.physicaldest is None:
      self.physicaldest = self.dest
      for x in ['simplex', 'duplex']:
        self.physicaldest = self.physicaldest.replace('-%s' % x, '')
    return self.physicaldest

  @classmethod
  def GetFromCUPS(cls, cj):
    """cj = cupsjob."""
    return cls(cj.dest, cj.id, cj.size, cj.state, cj.title, cj.user)

  @classmethod
  def GetJobs(cls, completed=False):
    return [cls.GetFromCUPS(x) for x in cupsext.getJobs(0, int(completed))]

  @classmethod
  def GetJobsForPrinter(cls, printer, completed=False):
    return [job for job in cls.GetJobs(completed) 
            if job.GetPhysicalDest() == printer]

class PrintQueue(object):
  def __init__(self, printer):
    self.alljobs = None
    self.printer = printer
    self.GetJobsForPrinter()

  def GetJobsForPrinter(self):
    self.alljobs = Job.GetJobsForPrinter(self.printer, completed=True)
    self.alljobs += Job.GetJobsForPrinter(self.printer, completed=False)
    self.alljobs.sort()
    self.alljobs.reverse()

  def PendingJobs(self):
    return [job for job in self.alljobs if not job.IsComplete()]

  def FinishedJobs(self):
    return [job for job in self.alljobs if job.IsComplete()]


if __name__ == '__main__':
  p = PrintQueue('renoir')
  print '=== Pending Jobs ==='
  for job in p.PendingJobs():
    print job

  print '=== Last 5 Completed Jobs ==='
  for job in p.FinishedJobs()[:5]:
    print job
