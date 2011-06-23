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

## Source step code for mercurial

from twisted.python import log
from twisted.internet import defer
from twisted.web.util import formatFailure

from buildbot.process import buildstep
from buildbot.steps.source import Source, _ComputeRepositoryURL
from buildbot.status.results import FAILURE, RETRY, EXCEPTION, Results
from buildbot.steps.source.exceptions import AbandonChain

class Mercurial(Source):
    """ Class for Mercurial with all the smarts """
    name = "hg"

    renderables = [ "repourl", "baseurl" ]

    def __init__(self, repourl=None, baseurl=None, mode='incremental', 
                 method=None, defaultBranch=None, branchType='inrepo', 
                 clobberOnBranchChange=True, **kwargs):

        """
        @type  repourl: string
        @param repourl: the URL which points at the Mercurial repository.
                        This uses the 'default' branch unless defaultBranch is
                        specified below and the C{branchType} is set to
                        'inrepo'.  It is an error to specify a branch without
                        setting the C{branchType} to 'inrepo'.

        @param baseurl: if 'dirname' branches are enabled, this is the base URL
                        to which a branch name will be appended. It should
                        probably end in a slash.  Use exactly one of C{repourl}
                        and C{baseurl}.

        @param defaultBranch: if branches are enabled, this is the branch
                              to use if the Build does not specify one
                              explicitly.
                              For 'dirname' branches, It will simply be
                              appended to C{baseurl} and the result handed to
                              the 'hg update' command.
                              For 'inrepo' branches, this specifies the named
                              revision to which the tree will update after a
                              clone.

        @param branchType: either 'dirname' or 'inrepo' depending on whether
                           the branch name should be appended to the C{baseurl}
                           or the branch is a mercurial named branch and can be
                           found within the C{repourl}

        @param clobberOnBranchChange: boolean, defaults to True. If set and
                                      using inrepos branches, clobber the tree
                                      at each branch change. Otherwise, just
                                      update to the branch.
        """
        
        self.repourl = repourl
        self.baseurl = baseurl
        self.branch = defaultBranch
        self.branchType = branchType
        self.method = method
        self.clobberOnBranchChange = clobberOnBranchChange
        Source.__init__(self, **kwargs)
        self.mode = mode
        self.addFactoryArguments(repourl=repourl,
                                 baseurl=baseurl,
                                 mode=mode,
                                 method=method,
                                 defaultBranch=defaultBranch,
                                 branchType=branchType,
                                 )

        assert self.mode in ['incremental', 'full']

        if repourl and baseurl:
            raise ValueError("you must provide exactly one of repourl and"
                             " baseurl")
        self.repourl = self.repourl and _ComputeRepositoryURL(self.repourl)
        self.baseurl = self.baseurl and _ComputeRepositoryURL(self.baseurl)
        
    def startVC(self, branch, revision, patch):
        
        slavever = self.slaveVersion('hg')
        if not slavever:
            raise BuildSlaveTooOldError("slave is too old, does not know "
                                        "about hg")
        self.branch = branch or 'default'
        self.revision = revision

        if branch:
            assert self.branchType == 'dirname' and not self.repourl
            # The restriction is we can't configure named branch here.
            # that's why 'not self.repourl'.
            self.repourl = self.baseurl + (branch or '')
        else:
            assert self.branchType == 'inrepo' and not self.baseurl
        self.stdio_log = self.addLog("stdio")

        if self.mode == 'incremental':
            d = self.incremental()
        elif self.mode == 'full':
            d = self.full()
        d.addCallback(self.parseGotRevision)
        d.addCallback(self.finish)
        d.addErrback(self.failed)

    def clean(self, _):
        command = ['--config', 'extensions.purge=', 'purge']
        d =  self._dovccmd(command)
        d.addCallback(self._pullUpdate)
        return d

    def clobber(self, _):
        cmd = buildstep.LoggedRemoteCommand('rmdir', {'dir': self.workdir})
        cmd.useLog(self.stdio_log, False)
        d = self.runCommand(cmd)
        d.addCallback(lambda _: self._dovccmd(['clone', '--noupdate'
                                               , self.repourl, "."]))
        d.addCallback(self._update)
        return d

    def failed(self, why):
        # copied from buildstep. changed exception to failure
        log.msg("BuildStep.failed, traceback follows")
        log.err(why)
        try:
            if self.progress:
                self.progress.finish()
            self.addHTMLLog("err.html", formatFailure(why))
            self.addCompleteLog("err.text", why.getTraceback())
            self.step_status.setText(["failed"])
            self.step_status.setText2([self.name])
            self.step_status.stepFinished(FAILURE)
        except:
            log.msg("exception during failure processing")
            log.err()

        try:
            self.releaseLocks()
        except:
            log.msg("exception while releasing locks")
            log.err()

        log.msg("BuildStep.failed now firing callback")
        self.deferred.callback(FAILURE)

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

    def fresh(self, _):
        command = ['--config', 'extensions.purge=', 'purge', '--all']
        d = self._dovccmd(command)
        d.addCallback(self._pullUpdate)
        return d

    def full(self):
        d = self._sourcedirIsUpdatable()
        def makeFullClone(updatable):
            if not updatable:
                log.msg("No mercurial repo present, making full clone")
                return self._dovccmd(['clone', self.repourl, '.',])
            else:
                return defer.succeed(0)
        d.addCallback(makeFullClone)

        if self.method == 'clean':
            d.addCallback(self.clean)
        elif self.method == 'fresh':
            d.addCallback(self.fresh)
        elif self.method == 'clobber':
            d.addCallback(self.clobber)
        return d

    def incremental(self):
        d = self._sourcedirIsUpdatable()
        def _cmd(updatable):
            if updatable:
                command = ['pull', self.repourl]
            else:
                command = ['clone', self.repourl, '.', '--noupdate']
            return command

        d.addCallback(_cmd)
        d.addCallback(self._dovccmd)
        d.addCallback(self._checkBranchChange)
        return d

    def parseGotRevision(self, _):
        d = self._dovccmd(['identify', '--id', '--debug'])
        def _setrev(res):
            revision = self.getLog('stdio').readlines()[-1].strip()
            if len(revision) != 40:
                return FAILURE
            log.msg("Got Mercurial revision %s" % (revision, ))
            self.setProperty('got_revision', revision, 'Source')
            return res
        d.addCallback(_setrev)
        return d

    def _checkBranchChange(self, _):
        d = self._getCurrentBranch()
        def _compare(current_branch):
            msg = "Working dir is on in-repo branch '%s' and build needs '%s'." % \
                (current_branch, self.branch)
            if current_branch != self.branch:
                if self.clobberOnBranchChange:
                    msg += ' Clobbering.'
                    log.msg(msg)
                    return self.clobber()
                else:
                    msg += ' Updating.'
                    log.msg(msg)
                    return self._update(None)
            else:
                msg += ' Updating.'
                log.msg(msg)
                return self._update(None)
        d.addCallback(_compare)
        return d

    def _pullUpdate(self, res):
        command = ['pull' , self.repourl, '--branch', self.branch]
        d = self._dovccmd(command)
        d.addCallback(self._checkBranchChange)
        return d

    def _dovccmd(self, command):
        cmd = buildstep.RemoteShellCommand(self.workdir, ['hg', '--verbose'] + command)
        cmd.useLog(self.stdio_log, False)
        log.msg("Starting mercurial command : hg %s" % (" ".join(command), ))
        d = self.runCommand(cmd)
        def evaluateCommand(cmd):
            if cmd.rc != 0:
                log.msg("Source step failed while running command %s" % cmd)
                raise AbandonChain(cmd.rc)
            return cmd.rc
        d.addCallback(lambda _: evaluateCommand(cmd))
        return d

    def _getCurrentBranch(self):
        d = self._dovccmd(['identify', '--branch'])
        def _getbranch(res):
            branch = self.getLog('stdio').readlines()[-1].strip()
            log.msg("Current branch is %s" % (branch, ))
            return branch
        d.addCallback(_getbranch).addErrback
        return d

    def _sourcedirIsUpdatable(self):
        cmd = buildstep.LoggedRemoteCommand('stat', {'file': self.workdir + '/.hg'})
        cmd.useLog(self.stdio_log, False)
        d = self.runCommand(cmd)
        def _fail(tmp):
            if cmd.rc != 0:
                return False
            return True
        d.addCallback(_fail)
        return d

    def _update(self, _):
        command = ['update', '--clean']
        if self.revision:
            command += ['--rev', self.revision]
        else:
            command += ['--rev', self.branch or 'default']
        d = self._dovccmd(command)
        return d
