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

import mock
from twisted.trial import unittest
from twisted.internet import defer
from twisted.python import failure
from buildbot.steps import shell
from buildbot.process import buildstep
from buildbot.status.results import SKIPPED, SUCCESS


DEFAULT_TIMEOUT="DEFAULT_TIMEOUT"
DEFAULT_MAXTIME="DEFAULT_MAXTIME"
DEFAULT_USEPTY="DEFAULT_USEPTY"

class FakeRemoteCommand(object):

    def __init__(self, remote_command, args):
        # copy the args and set a few defaults
        self.remote_command = remote_command
        self.args = args.copy()

    def run(self, step, remote):
        return self.testcase.fakeRunRemoteCommand(self, step, remote)


class FakeLoggedRemoteCommand(FakeRemoteCommand):

    def __init__(self, *args, **kwargs):
        FakeRemoteCommand.__init__(self, *args, **kwargs)
        self.logs = {}
        self.rc = -999

    def useLog(self, loog, closeWhenFinished=False, logfileName=None):
        if not logfileName:
            logfileName = loog.getName()
        self.logs[logfileName] = loog


class FakeRemoteShellCommand(FakeLoggedRemoteCommand):

    def __init__(self, workdir, command, env=None,
                 want_stdout=1, want_stderr=1,
                 timeout=DEFAULT_TIMEOUT, maxTime=DEFAULT_MAXTIME, logfiles={},
                 usePTY=DEFAULT_USEPTY, logEnviron=True):
        args = dict(workdir=workdir, command=command, env=env or {},
                want_stdout=want_stdout, want_stderr=want_stderr,
                timeout=timeout, maxTime=maxTime, logfiles=logfiles,
                usePTY=usePTY, logEnviron=logEnviron)
        FakeLoggedRemoteCommand.__init__(self, "shell", args)


class FakeLogFile(object):
    def __init__(self, name):
        self.name = name
        self.header = ''
        self.stdout = ''
        self.stderr = ''

    def getName(self):
        return self.name

    def addHeader(self, data):
        self.header += data

    def addStdout(self, data):
        self.stdout += data

    def addStderr(self, data):
        self.stderr += data

    def readlines(self): # TODO: remove channel arg from logfile.py
        return self.stdout.split('\n')

    def getText(self):
        return self.stdout


class Expect(object):
    """
    Define an expected L{RemoteCommand}, with the same arguments
    """

    def __init__(self, remote_command, args):
        """
        Expect a command named C{remote_command}, with args C{args}.
        """
        self.remote_command = remote_command
        self.args = args
        self.result = None

    def fakeRun(self, command):
        return defer.succeed(self)


class ExpectLogged(Expect):
    """
    Define an expected L{LoggedRemoteCommand}, with the same arguments

    Extra attributes of the logged remote command can be added to
    the instance, using class methods to specify the attributes::

        ExpectLogged('somecommand', { args='foo' })
            + ExpectLogged.log('stdio', stdout='foo!')
            + ExpectLogged.log('config.log', stdout='some info')
            + 0,      # (specifies the rc)
        ...

    """
    def __init__(self, remote_command, args):
        Expect.__init__(self, remote_command, args)
        self.updates = []

    @classmethod
    def log(self, name, **streams):
        return ('log', name, streams)

    def __add__(self, other):
        if isinstance(other, int):
            self.updates.append(('rc', other))
        elif isinstance(other, failure.Failure):
            self.updates.append(('err', other))
        else:
            self.updates.append(other)
        return self

    def fakeRun(self, command):
        # apply updates
        for upd in self.updates:
            if upd[0] == 'rc':
                command.rc = upd[1]
            elif upd[0] == 'err':
                return defer.fail(upd[1])
            elif upd[0] == 'log':
                name, streams = upd[1:]
                if 'header' in streams:
                    command.logs[name].addHeader(streams['header'])
                if 'stdout' in streams:
                    command.logs[name].addStdout(streams['stdout'])
                if 'stderr' in streams:
                    command.logs[name].addStderr(streams['stderr'])
        return Expect.fakeRun(self, command)


class ExpectShell(ExpectLogged):
    """
    Define an expected L{RemoteShellCommand}, with the same arguments Any
    non-default arguments must be specified explicitly (e.g., usePTY).
    """
    def __init__(self, workdir, command, env={},
                 want_stdout=1, want_stderr=1,
                 timeout=DEFAULT_TIMEOUT, maxTime=DEFAULT_MAXTIME, logfiles={},
                 usePTY=DEFAULT_USEPTY, logEnviron=True):
        args = dict(workdir=workdir, command=command, env=env,
                want_stdout=want_stdout, want_stderr=want_stderr,
                timeout=timeout, maxTime=maxTime, logfiles=logfiles,
                usePTY=usePTY, logEnviron=logEnviron)
        ExpectLogged.__init__(self, "shell", args)


class TestExecution(unittest.TestCase):

    def setUp(self):
        FakeRemoteCommand.testcase = self
        self.patch(buildstep, 'RemoteCommand', FakeRemoteCommand)
        self.patch(buildstep, 'LoggedRemoteCommand', FakeLoggedRemoteCommand)
        self.patch(buildstep, 'RemoteShellCommand', FakeRemoteShellCommand)
        self.expected_remote_commands = []

    def tearDown(self):
        del FakeRemoteCommand.testcase

    # utilities

    def setupStep(self, step, slave_version="99.99", slave_env={}):
        """
        Set up C{step} for testing.  This begins by using C{step} as a factor
        to create a I{new} step instance, thereby testing that the the factory
        arguments are handled correctly.  It then creates a comfortable
        environment for the slave to run in, repleate with a fake build and a
        fake slave.

        @param slave_version: slave version to present; defaults to "99.99"

        @param slave_env: environment from the slave at slave startup

        """
        # yes, Virginia, "factory" refers both to the tuple and its first
        # element TODO: fix that up
        factory, args = step.getStepFactory()
        step = self.step = factory(**args)

        # step.build

        b = mock.Mock(name="build")
        b.render = lambda x : x # render is identity
        b.getSlaveCommandVersion = lambda command, oldversion : slave_version
        b.slaveEnvironment = slave_env.copy()
        step.setBuild(b)

        # step.progress

        p = step.progress = mock.Mock(name="progress")

        # step.buildslave

        bs = step.buildslave = mock.Mock(name="buildslave")

        # step.step_status

        ss = mock.Mock(name="step_status")

        ss.status_text = None
        ss.logs = {}

        def ss_setText(strings):
            ss.status_text = strings
        ss.setText = ss_setText

        ss.getLogs = lambda : ss.logs

        self.step.setStepStatus(ss)

        # step overrides

        def addLog(name):
            l = FakeLogFile(name)
            ss.logs[name] = l
            return l
        step.addLog = addLog

        return step

    def expectCommands(self, *exp):
        """
        Add to the expected remote commands, along with their results.  Each
        argument should be an instance of L{Expect}.
        """
        self.expected_remote_commands.extend(exp)

    def expectOutcome(self, result, status_text):
        self.exp_outcome = dict(result=result, status_text=status_text)

    def runStep(self):
        """
        Run the step set up with L{setupStep}.

        @returns: Deferred that fires with the result of startStep
        """
        self.remote = mock.Mock(name="SlaveBuilder(remote)")
        d = self.step.startStep(self.remote)
        def check(result):
            self.assertEqual(self.expected_remote_commands, [],
                             "assert all expected commands were run")
            got_outcome = dict(result=result,
                        status_text=self.step.step_status.status_text)
            self.assertEqual(got_outcome, self.exp_outcome)
        d.addCallback(check)
        return d

    # callbacks from the running step

    def fakeRunRemoteCommand(self, command, step, remote):
        self.assertEqual(step, self.step)
        self.assertEqual(remote, self.remote)
        got = (command.remote_command, command.args)

        if not self.expected_remote_commands:
            self.fail("got command %r when no further commands were expected"
                    % (got,))
        exp = self.expected_remote_commands.pop(0)
        self.assertEqual(got, (exp.remote_command, exp.args))

        # let the Expect object show any behaviors that are required
        return exp.fakeRun(command)

    # assertions

    def assertStatusText(self, text):
        self.assertEqual(self.step.step_status.status_text, text)

    # tests

    def test_doStepIf_False(self):
        self.setupStep(shell.ShellCommand(command="echo hello", doStepIf=False))
        self.expectOutcome(result=SKIPPED,
                status_text=["'echo", "hello'", "skipped"])
        return self.runStep()

    def test_simple(self):
        self.setupStep(shell.ShellCommand(workdir='build',
                                          command="echo hello"))
        self.expectCommands(
            ExpectShell(workdir='build', command='echo hello',
                         usePTY="slave-config")
            + ExpectShell.log('stdio', header='this is a header')
            + ExpectShell.log('stdio', stdout='hello')
            + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=["'echo", "hello'"])
        return self.runStep()

