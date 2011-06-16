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
from buildbot.steps.source import mercurial
from buildbot.status.results import SUCCESS
from buildbot.test.util import sourcesteps
from buildbot.test.fake.remotecommand import ExpectShell, Expect


class TestMercurial(sourcesteps.SourceStepMixin, unittest.TestCase):

    def setUp(self):
        return self.setUpSourceStep()

    def tearDown(self):
        return self.tearDownSourceStep()

    def test_mode_clean(self):
        self.setupStep(
                mercurial.Mercurial(repourl='http://hg.mozilla.org',
                                    mode='full', method='clean'))
        self.expectCommands(
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', '--config',
                                 'extensions.purge=', 'purge'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'pull',
                                 'http://hg.mozilla.org'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'update',
                                 '--clean', '--rev', 'default'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'identify',
                                    '--id', '--debug'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_clobber(self):
        self.setupStep(
                mercurial.Mercurial(repourl='http://hg.mozilla.org',
                                    mode='full', method='clobber'))
        self.expectCommands(
            Expect('rmdir', dict(dir='wkdir')),
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'clone', '--noupdate',
                                    'http://hg.mozilla.org', '.'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'update',
                                 '--clean', '--rev', 'default'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'identify',
                                    '--id', '--debug'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_incremental(self):
        self.setupStep(
                mercurial.Mercurial(repourl='http://hg.mozilla.org',
                                    mode='incremental'))
        self.expectCommands(
            Expect('stat', dict(file='wkdir/.hg')),
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'clone',
                                 'http://hg.mozilla.org', '.'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'identify', '--branch'])
            + ExpectShell.log('stdio', stdout='default')
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'update', '--clean',
                                 '--rev', 'default'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'identify',
                                    '--id', '--debug'])
            + ExpectShell.log('stdio', stdout='\n')
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
            )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()

    def test_mode_fresh(self):
        self.setupStep(
                mercurial.Mercurial(repourl='http://hg.mozilla.org',
                                    mode='full', method='fresh'))
        self.expectCommands(
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', '--config',
                                 'extensions.purge=', 'purge', '--all'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'pull',
                                 'http://hg.mozilla.org'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'update',
                                 '--clean', '--rev', 'default'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['hg', '--verbose', 'identify',
                                    '--id', '--debug'])
            + ExpectShell.log('stdio',
                stdout='f6ad368298bd941e934a41f3babc827b2aa95a1d')
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        return self.runStep()
