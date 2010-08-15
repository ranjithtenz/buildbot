from zope.interface import implements

from buildslave.runprocess import RunProcess
from buildslave.interfaces import ISlaveOperations

class LocalSlaveOperations(object):
    implements(ISlaveOperations)

    def __init__(self, builder, command):
        self.builder = builder
        self.command = command

        self.last_stdout = None
        self.last_stderr = None

    def runprocess(self, workdir, environ=None,
                 sendStdout=True, sendStderr=True, sendRC=True,
                 timeout=None, maxTime=None, initialStdin=None,
                 keepStdinOpen=False, keepStdout=False, keepStderr=False,
                 logEnviron=True, logfiles={}, usePTY="slave-config"):
        rp = RunProcess(self.builder, self.command, workdir,
                sendStdout=sendStdout, sendStderr=sendStderr, sendRC=sendRC,
                timeout=timeout, maxTime=maxTime, initialStdin=initialStdin,
                keepStdinOpen=keepStdinOpen, keepStdout=keepStdout, keepStderr=keepStderr,
                logEnviron=logEnviron, logfiles=logfiles, usePTY=usePTY)
        d = rp.start()

        self.last_stdout = None
        def cb(res):
            self.last_stdout = rp.stdout
            return res
        if keepStdout:
            d.addCallback(cb)

        self.last_stderr = None
        def cb(res):
            self.last_stderr = rp.stderr
            return res
        if keepStderr:
            d.addCallback(cb)

        return d

    def getStdout(self):
        return self.last_stdout

    def getStderr(self):
        return self.last_stderr
