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

from twisted.trial import unittest
from twisted.python import failure
from buildbot.steps.source import git
from buildbot.status.results import SUCCESS
from buildbot.test.util import sourcesteps
from buildbot.test.fake.remotecommand import ExpectShell, Expect


class TestGit(sourcesteps.SourceStepMixin, unittest.TestCase):

    def setUp(self):
        return self.setUpSourceStep()

    def tearDown(self):
        return self.tearDownSourceStep()

    def test_mode_clean(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                                    mode='full', method='clean'))
        self.expectCommands(
            Expect('stat', dict(file='wkdir/.git'))
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'clean', '-f', '-d'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', '-t',
                                 'http://github.com/buildbot/buildbot.git',
                                 'master'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'FETCH_HEAD'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_clean_no_existing_repo(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                                    mode='full', method='clean'))
        self.expectCommands(
            Expect('stat', dict(file='wkdir/.git'))
            + 1,
            ExpectShell(workdir='wkdir',
                        command=['git', 'clone', 
                                 'http://github.com/buildbot/buildbot.git', '.'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'clean', '-f', '-d'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', '-t',
                                 'http://github.com/buildbot/buildbot.git',
                                 'master'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'FETCH_HEAD'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_clobber(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                        mode='full', method='clobber', progress=True))

        self.expectCommands(
            Expect('rmdir', dict(dir='wkdir')),
            ExpectShell(workdir='wkdir',
                        command=['git', 'clone', 
                                 'http://github.com/buildbot/buildbot.git',
                                 '.', '--progress'])
            +0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_incremental(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                                    mode='incremental'))
        self.expectCommands(
            Expect('stat', dict(file='wkdir/.git'))
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', '-t',
                                 'http://github.com/buildbot/buildbot.git',
                                 'master'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'FETCH_HEAD'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,

        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_fresh(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                                    mode='full', method='fresh'))
        self.expectCommands(
            Expect('stat', dict(file='wkdir/.git'))
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'clean', '-f', '-d', '-x'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', '-t',
                                 'http://github.com/buildbot/buildbot.git',
                                 'master'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'FETCH_HEAD'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_fresh_no_existing_repo(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                                    mode='full', method='fresh'))
        self.expectCommands(
            Expect('stat', dict(file='wkdir/.git'))
            + 1,
            ExpectShell(workdir='wkdir',
                        command=['git', 'clone', 
                                 'http://github.com/buildbot/buildbot.git', '.'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'clean', '-f', '-d', '-x'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', '-t',
                                 'http://github.com/buildbot/buildbot.git',
                                 'master'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'FETCH_HEAD'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_incremental_given_revision(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                                    mode='incremental'), dict(
                revision='abcdef01',
                ))
        self.expectCommands(
            Expect('stat', dict(file='wkdir/.git'))
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'cat-file', '-e', 'abcdef01'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'abcdef01'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_fresh_submodule(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                                    mode='full', method='fresh', submodule=True))
        self.expectCommands(
            Expect('stat', dict(file='wkdir/.git'))
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'clean', '-f', '-d', '-x'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', '-t',
                                 'http://github.com/buildbot/buildbot.git',
                                 'master'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'FETCH_HEAD'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'submodule', 'update', '--recursive'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'submodule', 'foreach', 'git', 'clean',
                                 '-f', '-d', '-x'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_clobber_shallow(self):
        self.setupStep(
                git.Git(repourl='http://github.com/buildbot/buildbot.git',
                        mode='full', method='clobber', shallow=True))

        self.expectCommands(
            Expect('rmdir', dict(dir='wkdir')),
            ExpectShell(workdir='wkdir',
                        command=['git', 'clone', '--depth', '1',
                                 'http://github.com/buildbot/buildbot.git',
                                 '.'])
            +0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()
