
from zope.interface import Interface

class ISlaveCommand(Interface):
    """This interface is implemented by all of the buildslave's Command
    subclasses. It specifies how the buildslave can start, interrupt, and
    query the various Commands running on behalf of the buildmaster."""

    def __init__(builder, stepId, args):
        """Create the Command. 'builder' is a reference to the parent
        buildbot.bot.SlaveBuilder instance, which will be used to send status
        updates (by calling builder.sendStatus). 'stepId' is a random string
        which helps correlate slave logs with the master. 'args' is a dict of
        arguments that comes from the master-side BuildStep, with contents
        that are specific to the individual Command subclass.

        This method is not intended to be subclassed."""

    def setup(args):
        """This method is provided for subclasses to override, to extract
        parameters from the 'args' dictionary. The default implemention does
        nothing. It will be called from __init__"""

    def start():
        """Begin the command, and return a Deferred.

        While the command runs, it should send status updates to the
        master-side BuildStep by calling self.sendStatus(status). The
        'status' argument is typically a dict with keys like 'stdout',
        'stderr', and 'rc'.

        When the step completes, it should fire the Deferred (the results are
        not used). If an exception occurs during execution, it may also
        errback the deferred, however any reasonable errors should be trapped
        and indicated with a non-zero 'rc' status rather than raising an
        exception. Exceptions should indicate problems within the buildbot
        itself, not problems in the project being tested.

        """

    def interrupt():
        """This is called to tell the Command that the build is being stopped
        and therefore the command should be terminated as quickly as
        possible. The command may continue to send status updates, up to and
        including an 'rc' end-of-command update (which should indicate an
        error condition). The Command's deferred should still be fired when
        the command has finally completed.

        If the build is being stopped because the slave it shutting down or
        because the connection to the buildmaster has been lost, the status
        updates will simply be discarded. The Command does not need to be
        aware of this.

        Child shell processes should be killed. Simple ShellCommand classes
        can just insert a header line indicating that the process will be
        killed, then os.kill() the child."""

class ISlaveOperations(Interface):
    """

    An object which can perform various filesystem-related operations on the
    slave.  Rather than access things directly, slave commands use an instance
    of this class.

    This has two benefits: first, it allows testing the commands in a simulated
    environment; second, it means that commands are designed in such a way that
    they need not exist on the system where the operations are actually carried
    out.

    """

    def runprocess(workdir, environ=None,
                 sendStdout=True, sendStderr=True, sendRC=True,
                 timeout=None, maxTime=None, initialStdin=None,
                 keepStdinOpen=False, keepStdout=False, keepStderr=False,
                 logEnviron=True, logfiles={}, usePTY="slave-config"):
        """

        Run an external process.

        @param workdir: directory in which to run the process

        @param environ: environment dictionary, or None to use the existing environment

        @param sendStdout: true to send stdout back to the buildmaster

        @param sendStderr: true to send stderr back to the buildmaster

        @param sendRC: true to send an 'rc' result to the buildmaster,
        signalling the end of the command

        @param timeout: timeout, in seconds, for data from the command, or None
        for no timeout.  If the command is silent for this duration, it will be
        aborted.  None for no timeout.

        @param maxTime: timeout, in seconds, for the entire command.
        Regardless of output, if the command runs for longer than this, it will
        be aborted.  None for no timeout.

        @param initialStdin: value to write to the process's stdin after
        starting (a string).  None for no input.

        @param keepStdinOpen: false to close stdin before the process starts,
        so it will get an EOF if it attempts to read.  Default true.

        @param keeptStdout: true to keep stdout - see the getStdout method

        @param keepStderr: true to keep stderr - see the getStderr method

        @param logEnviron: true to log the environment with 'header' messages;
        default true

        @param logfiles: dictionary mapping name to filename for additional
        logfiles to watch

        @param usePTY: whether or not to allocate a pty for this command; true
        or false force the value, while 'slave-config' (the default) uses the
        user's configured value from the SlaveBuilder.

        @return: Deferred which will fire with the exit code when the command
        completes.

        """

    def getStdout():
        """

        Get the stdout of the most recent runprocess invocation, if keepStdout
        was true

        """

    def getStderr():
        """

        Get the stderr of the most recent runprocess invocation, if keepStderr
        was true

        """
