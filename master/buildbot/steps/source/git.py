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

from twisted.python import log, failure
from twisted.internet import defer
from twisted.web.util import formatFailure

from buildbot.process import buildstep
from buildbot.steps.source import Source, _ComputeRepositoryURL
from buildbot.status.results import FAILURE
from buildbot.steps.source.exceptions import AbandonChain

class Git(Source):
    """ Class for Git with all the smarts """
    name='git'
    renderables = [ "repourl"]

    def __init__(self, repourl=None, branch='master', mode='incremental',
                 method=None,ignore_ignores=None, submodule=False,
                 shallow=False, progress=False, retryFetch=True, **kwargs):
        """
        @type  repourl: string
        @param repourl: the URL which points at the git repository

        @type  branch: string
        @param branch: The branch or tag to check out by default. If
                       a build specifies a different branch, it will
                       be used instead of this.

        @type  submodules: boolean
        @param submodules: Whether or not to update (and initialize)
                       git submodules.

        @type  mode: string
        @param mode: Type of checkout. Described in docs.

        @type  method: string
        @param method: Full builds can be done is different ways. This parameter
                       specifies which method to use.

        @type  progress: boolean
        @param progress: Pass the --progress option when fetching. This
                         can solve long fetches getting killed due to
                         lack of output, but requires Git 1.7.2+.
        @type  shallow: boolean
        @param shallow: Use a shallow or clone, if possible
        """

        self.branch    = branch
        self.method    = method
        self.prog  = progress
        self.repourl   = repourl
        self.retryFetch = retryFetch
        self.submodule = submodule
        self.shallow   = shallow
        self.fetchcount = 0
        Source.__init__(self, **kwargs)
        self.addFactoryArguments(branch=branch,
                                 mode=mode,
                                 method=method,
                                 progress=progress,
                                 repourl=repourl,
                                 submodule=submodule,
                                 shallow=shallow,
                                 retryFetch=retryFetch,
                                 )

        self.mode = mode
        self.repourl = self.repourl and _ComputeRepositoryURL(self.repourl)
        assert self.mode in ['incremental', 'full']
        if self.mode == 'full':
            assert self.method in ['clean', 'fresh', 'clobber']
        
    def startVC(self, branch, revision, patch):
        
        slavever = self.slaveVersion('git')
        if not slavever:
            raise BuildSlaveTooOldError("slave is too old, does not know "
                                        "about git")
        self.branch = branch or 'master'
        self.revision = revision
        self.stdio_log = self.addLog("stdio")

        if self.mode == 'incremental':
            d = self.incremental()
        elif self.mode == 'full':
            d = self.full()

        d.addCallback(self.parseGotRevision)
        d.addCallback(self.finish)
        d.addErrback(self.failed)
        return d

    def clean(self, _):
        command = ['clean', '-f', '-d']
        d = self._dovccmd(command)
        d.addCallback(self._fetch)
        d.addCallback(self._updateSubmodule)
        d.addCallback(self._cleanSubmodule)
        return d

    def clobber(self, _):
        cmd = buildstep.LoggedRemoteCommand('rmdir', {'dir': self.workdir})
        cmd.useLog(self.stdio_log, False)
        d = self.runCommand(cmd)
        d.addCallback(lambda _: self._full())
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
        # This function and stepFailed does almost same thing
        # but invoked at different palces
        d = defer.succeed(res)
        def _gotResults(results):
            self.setStatus(self.cmd, results)
            log.msg("Closing log, sending result of the command %s " % \
                        (self.cmd))
            return results
        d.addCallback(_gotResults)
        d.addCallbacks(self.finished, self.checkDisconnect)
        return d

    def fresh(self, _):
        command = ['clean', '-f', '-d', '-x']
        d = self._dovccmd(command)
        d.addCallback(self._fetch)
        d.addCallback(self._updateSubmodule)
        d.addCallback(self._cleanSubmodule)
        return d

    def full(self):
        if self.method == 'clobber':
            return self.clobber(None)

        d = self._sourcedirIsUpdatable()
        def makeFullClone(updatable):
            if not updatable:
                log.msg("No git repo present, making full clone")
                return self._full()
            else:
                return defer.succeed(0)
        d.addCallback(makeFullClone)

        if self.method == 'clean':
            d.addCallback(self.clean)
        elif self.method == 'fresh':
            d.addCallback(self.fresh)
        return d

    def incremental(self):
        d = self._sourcedirIsUpdatable()
        def fetch(res):
            # if revision exits checkout to that revision
            # else fetch and update
            if res == 0:
                return self._dovccmd(['reset', '--hard', self.revision])
            else:
                return self._fetch(None)

        # rename the function
        def cmd(updatable):
            if updatable:
                if self.revision:
                    d = self._dovccmd(['cat-file', '-e', self.revision])
                else:
                    d = defer.succeed(1)
                d.addCallback(fetch)
            else:
                d = self._full()
            return d

        d.addCallback(cmd)
        d.addCallback(self._updateSubmodule)
        return d

    def parseGotRevision(self, _):
        d = self._dovccmd(['rev-parse', 'HEAD'])
        def setrev(res):
            revision = self.getLog('stdio').readlines()[-1].strip()
            if len(revision) != 40:
                return FAILURE
            log.msg("Got Git revision %s" % (revision, ))
            self.setProperty('got_revision', revision, 'Source')
            return res
        d.addCallback(setrev)
        return d

    def _dovccmd(self, command, abandonOnFailure=True):
        cmd = buildstep.RemoteShellCommand(self.workdir, ['git'] + command)
        cmd.useLog(self.stdio_log, False)
        log.msg("Starting git command : git %s" % (" ".join(command), ))
        d = self.runCommand(cmd)
        def evaluateCommand(cmd):
            if abandonOnFailure and cmd.rc == 0:
                log.msg("Source step failed while running command %s" % cmd)
                raise failure.Failure(cmd.rc)
            return cmd.rc
        d.addCallback(lambda _: evaluateCommand(cmd))
        return d

    def _fetch(self, _):
        self.fetchcount += 1
        if self.fetchcount > 3:
            raise Exception("More than 3 retries to fetch, aborting")
        command = ['fetch', '-t', self.repourl, self.branch]
        # If the 'progress' option is set, tell git fetch to output
        # progress information to the log. This can solve issues with
        # long fetches killed due to lack of output, but only works
        # with Git 1.7.2 or later.
        if self.prog:
            command.append('--progress')

        d = self._dovccmd(command)
        def checkout(_):
            if self.revision:
                rev = self.revision
            else:
                rev = 'FETCH_HEAD'
            command = ['reset', '--hard', rev]
            return self._dovccmd(command, not self.retryFetch)
        d.addCallback(checkout)
        def retry(res):
            if res != 0 and self.retryFetch:
                log.msg("Fetch failed, retry no: %s" % str(self.fetchcount))
                return self._fetch(None)
            else:
                return res
        d.addCallback(retry)
        return d

    def _full(self):
        if self.shallow:
            command = ['clone', '--depth', '1', self.repourl, '.']
        else:
            command = ['clone', self.repourl, '.']
        #Fix references
        if self.prog:
            command.append('--progress')
        d = self._dovccmd(command)
        # If revision specified checkout that revision
        if self.revision:
            d.addCallback(self._dovccmd(['reset', '--hard', self.revision]))
        # init and update submodules, recurisively. If there's not recursion
        # it will simply not do it.
        if self.submodule:
            d.addCallback(self._dovccmd(['submodule', 'update', '--init',
                                        '--recursive']))
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

    def _updateSubmodule(self, _):
        if self.submodule:
            return self._dovccmd(['submodule', 'update', '--recursive'])
        else:
            return defer.succeed(0)

    def _cleanSubmodule(self, _):
        if self.submodule:
            command = ['submodule', 'foreach', 'git', 'clean', '-f', '-d']
            if self.mode == 'full' and self.method == 'fresh':
                command.append('-x')
            return self._dovccmd(command)
        else:
            return defer.succeed(0)
