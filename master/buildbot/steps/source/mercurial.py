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

from buildbot.process.buildstep import LoggedRemoteCommand, RemoteShellCommand
from buildbot.steps.source import Source
from buildbot.status.results import SUCCESS, WARNINGS, FAILURE, SKIPPED, \
     EXCEPTION, RETRY, worst_status


class Mercurial(Source):
    """ Class for Mercurial with all the smarts """
    name = "hg"

    def __init__(self, repourl=None, baseURL=None, mode='incremental',defaultBranch=None,
                 branchType='inrepo', clobberOnBranchChange=True, **kwargs):

        """
        @type  repourl: string
        @param repourl: the URL which points at the Mercurial repository.
                        This uses the 'default' branch unless defaultBranch is
                        specified below and the C{branchType} is set to
                        'inrepo'.  It is an error to specify a branch without
                        setting the C{branchType} to 'inrepo'.

        @param baseURL: if 'dirname' branches are enabled, this is the base URL
                        to which a branch name will be appended. It should
                        probably end in a slash.  Use exactly one of C{repourl}
                        and C{baseURL}.

        @param defaultBranch: if branches are enabled, this is the branch
                              to use if the Build does not specify one
                              explicitly.
                              For 'dirname' branches, It will simply be
                              appended to C{baseURL} and the result handed to
                              the 'hg update' command.
                              For 'inrepo' branches, this specifies the named
                              revision to which the tree will update after a
                              clone.

        @param branchType: either 'dirname' or 'inrepo' depending on whether
                           the branch name should be appended to the C{baseURL}
                           or the branch is a mercurial named branch and can be
                           found within the C{repourl}

        @param clobberOnBranchChange: boolean, defaults to True. If set and
                                      using inrepos branches, clobber the tree
                                      at each branch change. Otherwise, just
                                      update to the branch.
        """
        
        self.repourl = repourl
        self.baseURL = baseURL
        self.branch = defaultBranch
        self.branchType = branchType
        self.clobberOnBranchChange = clobberOnBranchChange
        Source.__init__(self, **kwargs)
        self.mode = mode
        self.addFactoryArguments(repourl=repourl,
                                 baseURL=baseURL,
                                 mode=mode,
                                 defaultBranch=defaultBranch,
                                 branchType=branchType,
                                 )

        if repourl and baseURL:
            raise ValueError("you must provide exactly one of repourl and"
                             " baseURL")

    def startVC(self, branch, revision, patch):

        slavever = self.slaveVersion('hg')
        if not slavever:
            raise BuildSlaveTooOldError("slave is too old, does not know "
                                        "about hg")

        if self.repourl:
            assert self.branchType == 'inrepo'
            self.repourl = self.computeRepositoryURL(self.repourl)
        else:
            self.repourl = self.computeRepositoryURL(self.baseURL) + (self.branch or '')

        if branch:
            self.branch = branch

        assert self.mode in ['incremental', 'clobber', 'fresh']
        self.stdio_log = self.addLog("stdio")

        d = defer.succeed(None)
        if self.mode == 'incremental':
            d.addCallback(self.incremental)
        if self.mode == 'clobber':
            d.addCallback(self.doClobber)
        d.addCallback(self._parseGotRevision)
        return d

    def _dovccmd(self, command, end=True):
        self.cmd = cmd = RemoteShellCommand(self.workdir, ['hg', '--verbose'] + command)
        self.cmd.useLog(self.stdio_log, end)
        log.msg("Mercurial command : %s" % ("hg ".join(command), ))
        d = self.runCommand(self.cmd)
        if end:
            log.msg("Closing log, sending result of the command %s" % (self.cmd, ))
            def _gotResults(results):
                self.setStatus(self.cmd, results)
                return results
            d.addCallback(_gotResults)
            d.addCallback(lambda _: self.createSummary(self.cmd.logs['stdio']))
            d.addCallback(lambda _: self.evaluateCommand(self.cmd)) 
            d.addCallbacks(self.finished, self.checkDisconnect)
            d.addErrback(self.failed)
        return d

    def _sourcedirIsUpdatable(self, _):
        cmd = LoggedRemoteCommand('stat', {'file': self.workdir + '/.hg'})
        cmd.useLog(self.stdio_log, False)
        d = self.runCommand(cmd)
        def _fail(tmp):
            if cmd.rc == 1:
                return False
            return True
        d.addCallback(_fail)
        return d

    def doVCUpdate(self, _):
        d = defer.succeed(_)
        d.addCallback(self._sourcedirIsUpdatable)
        def cmd(updatable):
            if updatable:
                command = ['pull', '--update' , self.repourl]
            else:
                command = ["clone", self.repourl, "."]

            if self.branch:
                command += ['--branch', self.branch]
            return command

        d.addCallback(cmd)
        d.addCallback(self._dovccmd, False)
        return d

    def doClobber(self, _):
        self.cmd = LoggedRemoteCommand('rmdir', {'dir': self.workdir})
        self.cmd.useLog(self.stdio_log, False)
        d = self.runCommand(self.cmd)
        d.addCallback(lambda _: self._dovccmd(["clone", self.repourl, "."], False))
        return d

    def _parseGotRevision(self, _):
        d = defer.succeed(None)
        d.addCallback(lambda _: self._dovccmd(['identify', '--id', '--debug'], True))
        def _setrev(_):
            revision = self.getLog('stdio').readlines()[-1].strip()
            if len(revision) != 40:
                return None
            log.msg("Got Mercurial revision %s" % (revision, ))
            self.setProperty('got_revision', revision, 'Source')
            return revision
        d.addCallback(_setrev)
        return d

    def _getCurrentBranch(self, _):
        d = defer.succeed(None)
        d.addCallback(lambda _: self._dovccmd(['identify', '--branch'], False))
        def _getbranch(_):
            branch = self.getLog('stdio').readlines()[-1].strip()
            log.msg("Current branch is %s" % (branch, ))
            return branch
        d.addCallback(_getbranch)
        return d

    def incremental(self, _):
        self.action = None
        d = defer.succeed(_)
        d.addCallback(self._getCurrentBranch)
        def _compare(current_branch):
            if current_branch != self.branch:
                msg = "Working dir is on in-repo branch '%s' and build needs '%s'." % (current_branch, self.branch)
                if self.clobberOnBranchChange:
                    msg += ' Cloberring.'
                    self.action = self.doClobber(None)
                else:
                    msg += ' Updating.'
                    self.action = self.doVCUpdate(None)
                log.msg(msg)

        d.addCallback(_compare)
        d.addCallback(self.action)
        return d
