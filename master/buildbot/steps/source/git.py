# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

from twisted.python import log
from twisted.internet import defer

from buildbot.process import buildstep
from buildbot.steps.source import Source, _ComputeRepositoryURL
from buildbot.status.results import FAILURE
from buildslave.exceptions import AbandonChain

class Git(Source):
    """ Class for Git with all the smarts """
    name='git'

    renderables = [ "repourl" ]

    def __init__(self, repourl=None,
                 branch='master',
                 mode='incremental',
                 method=None,
                 ignore_ignores=None,
                 **kwargs):
        """
        @type  repourl: string
        @param repourl: the URL which points at the git repository

        @type  branch: string
        @param branch: The default to check branch. Default value 'master'


        """

        self.branch = branch
        self.repourl = repourl
        self.method = method
        Source.__init__(self, **kwargs)
        self.addFactoryArguments(repourl=repourl,
                                 mode=mode,
                                 method=method,
                                 )
        self.mode = mode
        self.repourl = self.repourl and _ComputeRepositoryURL(self.repourl)
        
    def startVC(self, branch, revision, patch):
        
        slavever = self.slaveVersion('git')
        if not slavever:
            raise BuildSlaveTooOldError("slave is too old, does not know "
                                        "about git")
        self.branch = branch or 'master'
        self.stdio_log = self.addLog("stdio")

        if self.mode == 'incremental':
            log.msg("fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
            d = self.incremental()
        d.addCallback(self.parseGotRevision)
        d.addCallback(self.finish)
        d.addErrback(self.failed)
        return d

    def incremental(self):
        d = self._sourcedirIsUpdatable()
        def _cmd(updatable):
            if updatable:
                command = ['pull', self.repourl]
            else:
                command = ['clone', self.repourl, '.']
            return command

        d.addCallback(_cmd)
        d.addCallback(self._dovccmd)
        d.addCallback(self._abandonOnFailure)
        return d

    def finish(self, res):
        d = defer.succeed(res)
        def _gotResults(results):
            self.setStatus(self.cmd, results)
            log.msg("Closing log, sending result of the command %s " % \
                        (self.cmd))
            return results
        d.addCallback(_gotResults)
        d.addCallbacks(self.finished, self.checkDisconnect)
        d.addErrback(self.failed)
        return d

    def parseGotRevision(self, _):
        d = self._dovccmd(['rev-parse', 'HEAD'])
        def _setrev(res):
            revision = self.getLog('stdio').readlines()[-1].strip()
            if len(revision) != 40:
                return FAILURE
            log.msg("Got Git revision %s" % (revision, ))
            self.setProperty('got_revision', revision, 'Source')
            return res
        d.addCallback(_setrev)
        return d

    def _abandonOnFailure(self, rc):
        if type(rc) is not int:
            log.msg("weird, _abandonOnFailure was given rc=%s (%s)" % \
                    (rc, type(rc)))
        assert isinstance(rc, int)
        if rc != 0:
            raise AbandonChain(rc)
        return rc

    def _dovccmd(self, command):
        cmd = buildstep.RemoteShellCommand(self.workdir, ['git'] + command)
        cmd.useLog(self.stdio_log, False)
        log.msg("Git command : %s" % ("git ".join(command), ))
        d = self.runCommand(cmd)
        def evaluateCommand(cmd):
            return cmd.rc
        d.addCallback(lambda _: evaluateCommand(cmd))
        d.addErrback(self.failed)
        return d

    def _sourcedirIsUpdatable(self):
        cmd = buildstep.LoggedRemoteCommand('stat', {'file': self.workdir + '/.git'})
        log.msg(self.workdir)
        cmd.useLog(self.stdio_log, False)
        d = self.runCommand(cmd)
        def _fail(tmp):
            if cmd.rc != 0:
                return False
            return True
        d.addCallback(_fail)
        return d
