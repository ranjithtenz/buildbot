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
    renderables = [ "repourl"]

    def __init__(self, repourl=None, branch='master', mode='incremental',
                 method=None,ignore_ignores=None, submodule=False,
                 progress=False, **kwargs):
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
        """

        self.branch    = branch
        self.method    = method
        self.progress  = progress
        self.repourl   = repourl
        self.submodule = submodule
        Source.__init__(self, **kwargs)
        self.addFactoryArguments(branch=branch,
                                 mode=mode,
                                 method=method,
                                 progress=progress,
                                 repourl=repourl,
                                 submodule=submodule,
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

    def clean(self):
        return defer.succeed(FAILURE)

    def clobber(self):
        return FAILURE

    def incremental(self):
        d = self._sourcedirIsUpdatable()
        def fetch(res):
            #if revision exits checkout to that revision
            # else fetch and update
            if res != 0:
                return self._dovccmd(['reset', '--hard', self.revision])
            else:
                return self._fetch()
            return d

        def cmd(updatable):
            d = defer.succeed(None)
            if updatable:
                if self.revision:
                    d.addCallback(self._dovccmd(['cat-file', '-e', self.revison]))
                else:
                    d.addCallback(lambda _: 1)
                d.addCallback(fetch)
            else:
                d.addCallback(self._full())
        d.addCallback(cmd)
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

    def fresh(self):
        return FAILURE

    def full(self):
        if self.method == 'clean':
            return self.clean()
        elif self.method == 'fresh':
            return self.fresh()
        elif self.method == 'clobber':
            return self.clobber()

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

    def _fetch(self):
        command = ['fetch', '-t', self.repourl, self.branch]
        # If the 'progress' option is set, tell git fetch to output
        # progress information to the log. This can solve issues with
        # long fetches killed due to lack of output, but only works
        # with Git 1.7.2 or later.
        if self.progress:
            command.append('--progress')
        d = self._dovccmd(command)
        def checkout():
            if self.revision:
                rev = self.revision
            else:
                rev = 'FETCH_HEAD'
            command = ['reset', '--hard', head]
            return self._dovccmd(command)
        d.addCallback(checkout)
        return d

    def _full(self):
        command = ['clone', self.repourl, '.']
        if self.progress:
            command.append('--progress')
        d = self._dovccmd(command)
        if self.revision:
            d.addCallback(self._dovccmd(['reset', '--hard', self.revision]))
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
