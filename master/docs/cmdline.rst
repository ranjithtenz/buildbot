This section describes command-line tools available after buildbot
installation. Since version 0.8 the one-for-all ``buildbot`` command-line tool
was divided into two parts namely ``buildbot`` and ``buildslave``. The last
one was separated from main command-line tool to minimize dependencies
required for running a buildslave while leaving all other functions to
``buildbot`` tool.

Every command-line tool has a list of global options and a set of commands
which have their own options. One can run these tools in the following way::

    buildbot [global options] @var{command} [command options]

Global options are the same for both tools which perform the following
actions:

:@code{--help}: Print general help about available commands and global
    options and exit. All subsequent arguments are ignored.

:@code{--verbose}: Set verbose output.

:@code{--version}: Print current buildbot version and exit. All
    subsequent arguments are ignored.

One can also get help on any command by specifying ``--help`` as a command
option::

    buildbot @var{command} --help

You can also use manual pages for ``buildbot`` and ``buildslave`` for quick
reference on command-line options.

buildbot
========

The ``buildbot`` command-line tool can be used to start or stop a buildmaster
and to interact with a running buildmaster. Some of its subcommands are
intended for buildmaster admins, while some are for developers who are editing
the code that the buildbot is monitoring.

Administrator Tools
-------------------

The following ``buildbot`` sub-commands are intended for buildmaster
administrators:

create-master
^^^^^^^^^^^^^

This creates a new directory and populates it with files that allow it to be
used as a buildmaster's base directory.

You will usually want to use the ``-r`` option to create a relocatable
``buildbot.tac``.  This allows you to move the master directory without
editing this file. ::

    buildbot create-master -r BASEDIR

start
^^^^^

This starts a buildmaster which was already created in the given base
directory. The daemon is launched in the background, with events logged to a
file named ``twistd.log``. ::

    buildbot start BASEDIR

stop
^^^^

This terminates the buildmaster running in the given directory. ::

    buildbot stop BASEDIR

sighup
^^^^^^

This sends a SIGHUP to the buildmaster running in the given directory, which
causes it to re-read its ``master.cfg`` file. ::

    buildbot sighup BASEDIR

Developer Tools
---------------

These tools are provided for use by the developers who are working on the code
that the buildbot is monitoring.

.. _statuslog:

statuslog
^^^^^^^^^ ::

    buildbot statuslog --master @var{MASTERHOST}:@var{PORT}

This command starts a simple text-based status client, one which just prints
out a new line each time an event occurs on the buildmaster.

The @option{--master} option provides the location of the
``buildbot.status.client.PBListener`` status port, used to deliver build
information to realtime status clients. The option is always in the form of a
string, with hostname and port number separated by a colon
(``HOSTNAME:PORTNUM``). Note that this port is *not* the same as the slaveport
(although a future version may allow the same port number to be used for both
purposes). If you get an error message to the effect of "Failure:
twisted.cred.error.UnauthorizedLogin:", this may indicate that you are
connecting to the slaveport rather than a ``PBListener`` port.

The @option{--master} option can also be provided by the ``masterstatus`` name
in ``.buildbot/options`` (see :ref:`-buildbot-config-directory`).

.. _statusgui:

statusgui
^^^^^^^^^

.. index::
    single: statusgui

If you have set up a PBListener (see :ref:`pblistener`), you will be able to
monitor your Buildbot using a simple Gtk+ application invoked with the
``buildbot statusgui`` command::

    buildbot statusgui --master @var{MASTERHOST}:@var{PORT}

This command starts a simple Gtk+-based status client, which contains a few
boxes for each Builder that change color as events occur. It uses the same
@option{--master} argument and ``masterstatus`` option as the ``buildbot
statuslog`` command (see :ref:`statuslog`).

.. _try:

try
^^^

This lets a developer to ask the question "What would happen if I committed
this patch right now?". It runs the unit test suite (across multiple build
platforms) on the developer's current code, allowing them to make sure they
will not break the tree when they finally commit their changes.

The ``buildbot try`` command is meant to be run from within a developer's
local tree, and starts by figuring out the base revision of that tree (what
revision was current the last time the tree was updated), and a patch that can
be applied to that revision of the tree to make it match the developer's copy.
This (revision, patch) pair is then sent to the buildmaster, which runs a
build with that SourceStamp. If you want, the tool will emit status messages
as the builds run, and will not terminate until the first failure has been
detected (or the last success).

There is an alternate form which accepts a pre-made patch file (typically the
output of a command like 'svn diff'). This "--diff" form does not require a
local tree to run from. See See :ref:`try`, concerning the "--diff" command
option.

For this command to work, several pieces must be in place: the See :ref:`try-
schedulers`, as well as some client-side configuration.

locating the master
"""""""""""""""""""

The ``try`` command needs to be told how to connect to the try scheduler, and
must know which of the authentication approaches described above is in use by
the buildmaster. You specify the approach by using @option{--connect=ssh} or
@option{--connect=pb} (or ``try_connect = 'ssh'`` or ``try_connect = 'pb'`` in
``.buildbot/options``).

For the PB approach, the command must be given a @option{--master} argument
(in the form HOST:PORT) that points to TCP port that you picked in the
``Try_Userpass`` scheduler. It also takes a @option{--username} and
@option{--passwd} pair of arguments that match one of the entries in the
buildmaster's ``userpass`` list. These arguments can also be provided as
``try_master``, ``try_username``, and ``try_password`` entries in the
``.buildbot/options`` file.

For the SSH approach, the command must be given @option{--host} and
@option{--username} to get to the buildmaster host. It must also be given
@option{--jobdir}, which points to the inlet directory configured above. The
jobdir can be relative to the user's home directory, but most of the time you
will use an explicit path like ``~buildbot/project/jobdir``. These arguments
can be provided in ``.buildbot/options`` as ``try_host``, ``try_username``,
and ``try_jobdir``.

In addition, the SSH approach needs to connect to a PBListener status port, so
it can retrieve and report the results of the build (the PB approach uses the
existing connection to retrieve status information, so this step is not
necessary). This requires a @option{--masterstatus} argument, or a
``try_masterstatus`` entry in ``.buildbot/options``, in the form of a
HOSTNAME:PORT string.

The following command line arguments are deprecated, but retained for backward
compatibility:

*   @option{--tryhost} is replaced by @option{--host}

*   @option{--trydir} is replaced by @option{--jobdir}

*   @option{--master} is replaced by @option{--masterstatus}

Likewise, the following ``.buildbot/options`` file entries are deprecated, but
retained for backward compatibility:

*   ``try_dir`` is replaced by ``try_jobdir``

*   ``masterstatus`` is replaced by ``try_masterstatus``

choosing the Builders
"""""""""""""""""""""

A trial build is performed on multiple Builders at the same time, and the
developer gets to choose which Builders are used (limited to a set selected by
the buildmaster admin with the TryScheduler's ``builderNames=`` argument). The
set you choose will depend upon what your goals are: if you are concerned
about cross-platform compatibility, you should use multiple Builders, one from
each platform of interest. You might use just one builder if that platform has
libraries or other facilities that allow better test coverage than what you
can accomplish on your own machine, or faster test runs.

The set of Builders to use can be specified with multiple @option{--builder}
arguments on the command line. It can also be specified with a single
``try_builders`` option in ``.buildbot/options`` that uses a list of strings
to specify all the Builder names::

    try_builders = ["full-OSX", "full-win32", "full-linux"]

If you are using the PB approach, you can get the names of the builders that
are configured for the try scheduler using the ``get-builder-names`` argument::

    buildbot try --get-builder-names --connect=pb --master=... --username=... --passwd=...

specifying the VC system
""""""""""""""""""""""""

The ``try`` command also needs to know how to take the developer's current
tree and extract the (revision, patch) source-stamp pair. Each VC system uses
a different process, so you start by telling the ``try`` command which VC
system you are using, with an argument like @option{--vc=cvs} or
@option{--vc=git}. This can also be provided as ``try_vc`` in
``.buildbot/options``.

The following names are recognized: ``bzr`` ``cvs`` ``darcs`` ``git`` ``hg``
``mtn`` ``p4`` ``svn``

finding the top of the tree
"""""""""""""""""""""""""""

Some VC systems (notably CVS and SVN) track each directory more-or-less
independently, which means the ``try`` command needs to move up to the top of
the project tree before it will be able to construct a proper full-tree patch.
To accomplish this, the ``try`` command will crawl up through the parent
directories until it finds a marker file. The default name for this marker
file is ``.buildbot-top``, so when you are using CVS or SVN you should ``touch
.buildbot-top`` from the top of your tree before running ``buildbot try``.
Alternatively, you can use a filename like ``ChangeLog`` or ``README``, since
many projects put one of these files in their top-most directory (and nowhere
else). To set this filename, use @option{--topfile=ChangeLog}, or set it in
the options file with ``try_topfile = 'ChangeLog'``.

You can also manually set the top of the tree with
@option{--topdir=~/trees/mytree}, or ``try_topdir = '~/trees/mytree'``. If you
use ``try_topdir``, in a ``.buildbot/options`` file, you will need a separate
options file for each tree you use, so it may be more convenient to use the
``try_topfile`` approach instead.

Other VC systems which work on full projects instead of individual directories
(darcs, mercurial, git, monotone) do not require ``try`` to know the top
directory, so the @option{--topfile} and @option{--topdir} arguments will be
ignored.

If the ``try`` command cannot find the top directory, it will abort with an
error message.

The following command line arguments are deprecated, but retained for backward
compatibility:

*   @option{--try-topdir} is replaced by @option{--topdir}

*   @option{--try-topfile} is replaced by @option{--topfile}

determining the branch name
"""""""""""""""""""""""""""

Some VC systems record the branch information in a way that "try" can locate
it.  For the others, if you are using something other than the default branch,
you will have to tell the buildbot which branch your tree is using. You can do
this with either the @option{--branch} argument, or a @option{try_branch}
entry in the ``.buildbot/options`` file.

determining the revision and patch
""""""""""""""""""""""""""""""""""

Each VC system has a separate approach for determining the tree's base
revision and computing a patch.

:CVS:

    ``try`` pretends that the tree is up to date. It converts the current time
    into a ``-D`` time specification, uses it as the base revision, and
    computes the diff between the upstream tree as of that point in time
    versus the current contents. This works, more or less, but requires that
    the local clock be in reasonably good sync with the repository.

:SVN: ``try`` does a ``svn status -u`` to find the latest repository
    revision number (emitted on the last line in the "Status against
    revision: NN" message). It then performs an ``svn diff -rNN`` to
    find out how your tree differs from the repository version, and
    sends the resulting patch to the buildmaster. If your tree is not
    up to date, this will result in the "try" tree being created with
    the latest revision, then *backwards* patches applied to bring it
    "back" to the version you actually checked out (plus your actual
    code changes), but this will still result in the correct tree
    being used for the build.

:bzr: ``try`` does a ``bzr revision-info`` to find the base revision,
    then a ``bzr diff -r$base..`` to obtain the patch.

:Mercurial: ``hg identify --debug`` emits the full revision id (as
    opposed to the common 12-char truncated) which is a SHA1 hash of
    the current revision's contents. This is used as the base
    revision. ``hg diff`` then provides the patch relative to that
    revision. For ``try`` to work, your working directory must only
    have patches that are available from the same remotely-available
    repository that the build process' ``source.Mercurial`` will use.

:Perforce: ``try`` does a ``p4 changes -m1 ...`` to determine the
    latest changelist and implicitly assumes that the local tree is
    synched to this revision. This is followed by a ``p4 diff -du`` to
    obtain the patch. A p4 patch differs sligtly from a normal diff.
    It contains full depot paths and must be converted to paths
    relative to the branch top. To convert the following restriction
    is imposed. The p4base (see see :ref:`p-source`)  is assumed to be
    ``//depot``

:Darcs: ``try`` does a ``darcs changes --context`` to find the list of
    all patches back to and including the last tag that was made. This
    text file (plus the location of a repository that contains all
    these patches) is sufficient to re-create the tree. Therefore the
    contents of this "context" file *are* the revision stamp for a
    Darcs-controlled source tree.  It then does a ``darcs diff -u`` to
    compute the patch relative to that revision.

:Git: ``git branch -v`` lists all the branches available in the local
    repository along with the revision ID it points to and a short
    summary of the last commit. The line containing the currently
    checked out branch begins with '* ' (star and space) while all the
    others start with '  ' (two spaces). ``try`` scans for this line
    and extracts the branch name and revision from it. Then it
    generates a diff against the base revision. @c TODO: I'm not sure
    if this actually works the way it's intended @c since the
    extracted base revision might not actually exist in the @c
    upstream repository. Perhaps we need to add a --remote option to
    @c specify the remote tracking branch to generate a diff against.

:Monotone: ``mtn automate get_base_revision_id`` emits the full
    revision id which is a SHA1 hash of the current revision's
    contents. This is used as the base revision. ``mtn diff`` then
    provides the patch relative to that revision.  For ``try`` to
    work, your working directory must only have patches that are
    available from the same remotely-available repository that the
    build process' ``source.Monotone`` will use.

showing who built
"""""""""""""""""

You can provide the @option{--who=dev} to designate who is running the try
build. This will add the ``dev`` to the Reason field on the try build's status
web page. You can also set ``try_who = dev`` in the ``.buildbot/options``
file. Note that @option{--who=dev} will not work on version 0.8.3 or earlier
masters.

waiting for results
"""""""""""""""""""

If you provide the @option{--wait} option (or ``try_wait = True`` in
``.buildbot/options``), the ``buildbot try`` command will wait until your
changes have either been proven good or bad before exiting. Unless you use the
@option{--quiet} option (or ``try_quiet=True``), it will emit a progress
message every 60 seconds until the builds have completed.

Sometimes you might have a patch from someone else that you want to submit to
the buildbot. For example, a user may have created a patch to fix some
specific bug and sent it to you by email. You've inspected the patch and
suspect that it might do the job (and have at least confirmed that it doesn't
do anything evil). Now you want to test it out.

One approach would be to check out a new local tree, apply the patch, run your
local tests, then use "buildbot try" to run the tests on other platforms. An
alternate approach is to use the ``buildbot try --diff`` form to have the
buildbot test the patch without using a local tree.

This form takes a @option{--diff} argument which points to a file that
contains the patch you want to apply. By default this patch will be applied to
the TRUNK revision, but if you give the optional @option{--baserev} argument,
a tree of the given revision will be used as a starting point instead of
TRUNK.

You can also use ``buildbot try --diff=-`` to read the patch from stdin.

Each patch has a "patchlevel" associated with it. This indicates the number of
slashes (and preceding pathnames) that should be stripped before applying the
diff. This exactly corresponds to the @option{-p} or @option{--strip} argument
to the ``patch`` utility. By default ``buildbot try --diff`` uses a patchlevel
of 0, but you can override this with the @option{-p} argument.

When you use @option{--diff}, you do not need to use any of the other options
that relate to a local tree, specifically @option{--vc}, @option{--topfile},
or @option{--topdir}. These options will be ignored. Of course you must still
specify how to get to the buildmaster (with @option{--connect},
@option{--host}, etc).

Other Tools
-----------

These tools are generally used by buildmaster administrators.

.. _sendchange:

sendchange
^^^^^^^^^^

This command is used to tell the buildmaster about source changes. It is
intended to be used from within a commit script, installed on the VC server.
It requires that you have a PBChangeSource (see :ref:`pbchangesource`) running
in the buildmaster (by being set in ``c['change_source']``). ::

    buildbot sendchange --master @var{MASTERHOST}:@var{PORT} --auth @var{USER}:@var{PASS} \
            --who @var{COMMITTER} @var{FILENAMES..}

The ``auth`` option specifies the credentials to use to connect to the master,
in the form ``user:pass``.  If the password is omitted, then sendchange will
prompt for it.  If both are omitted, the old default (username "change" and
password "changepw") will be used.  Note that this password is well-known, and
should not be used on an internet-accessible port.

The ``master`` and ``who`` arguments can also be given in the options file
(see :ref:`-buildbot-config-directory`).  There are other (optional) arguments
which can influence the ``Change`` that gets submitted:

:--branch: (or option ``branch``) This provides the (string) branch
    specifier. If omitted, it defaults to None, indicating the
    "default branch". All files included in this Change must be on the
    same branch.

:--category: (or option ``category``) This provides the (string)
    category specifier. If omitted, it defaults to None, indicating
    "no category". The category property can be used by Schedulers to
    filter what changes they listen to.

:--project: (or option ``project``) This provides the (string) project
    to which this change applies, and defaults to ".  The project can
    be used by schedulers to decide which builders should respond to a
    particular change.

:--repository: (or option ``repository``) This provides the repository
    from which this change came, and defaults to ".

:--revision: This provides a revision specifier, appropriate to the VC
    system in use.

:--revision_file: This provides a filename which will be opened and
    the contents used as the revision specifier. This is specifically
    for Darcs, which uses the output of ``darcs changes --context`` as
    a revision specifier. This context file can be a couple of
    kilobytes long, spanning a couple lines per patch, and would be a
    hassle to pass as a command-line argument.

:--property: This parameter is used to set a property on the Change
    generated by sendchange. Properties are specified as a name:value
    pair, separated by a colon. You may specify many properties by
    passing this parameter multiple times.

:--comments: This provides the change comments as a single argument.
    You may want to use @option{--logfile} instead.

:--logfile: This instructs the tool to read the change comments from
    the given file. If you use ``-`` as the filename, the tool will
    read the change comments from stdin.

:--encoding: Specifies the character encoding for all other
    parameters, defaulting to 'utf8'.

.. _debugclient:

debugclient
^^^^^^^^^^^ ::

    buildbot debugclient --master @var{MASTERHOST}:@var{PORT} --passwd @var{DEBUGPW}

This launches a small Gtk+/Glade-based debug tool, connecting to the
buildmaster's "debug port". This debug port shares the same port number as the
slaveport (see :ref:`setting-the-pb-port-for-slaves`), but the ``debugPort``
is only enabled if you set a debug password in the buildmaster's config file
(see :ref:`debug-options`). The @option{--passwd} option must match the
``c['debugPassword']`` value.

@option{--master} can also be provided in ``.debug/options`` by the ``master``
key. @option{--passwd} can be provided by the ``debugPassword`` key.  See :ref
:`-buildbot-config-directory`.

The ``Connect`` button must be pressed before any of the other buttons will be
active. This establishes the connection to the buildmaster. The other sections
of the tool are as follows:

:Reload .cfg: Forces the buildmaster to reload its ``master.cfg``
    file. This is equivalent to sending a SIGHUP to the buildmaster,
    but can be done remotely through the debug port. Note that it is a
    good idea to be watching the buildmaster's ``twistd.log`` as you
    reload the config file, as any errors which are detected in the
    config file will be announced there.

:Rebuild .py: (not yet implemented). The idea here is to use Twisted's
    "rebuild" facilities to replace the buildmaster's running code
    with a new version. Even if this worked, it would only be used by
    buildbot developers.

:poke IRC: This locates a ``words.IRC`` status target and causes it to
    emit a message on all the channels to which it is currently
    connected. This was used to debug a problem in which the
    buildmaster lost the connection to the IRC server and did not
    attempt to reconnect.

:Commit: This allows you to inject a Change, just as if a real one had
    been delivered by whatever VC hook you are using. You can set the
    name of the committed file and the name of the user who is doing
    the commit. Optionally, you can also set a revision for the
    change. If the revision you provide looks like a number, it will
    be sent as an integer, otherwise it will be sent as a string.

:Force Build: This lets you force a Builder (selected by name) to
    start a build of the current source tree.

:Currently: (obsolete). This was used to manually set the status of
    the given Builder, but the status-assignment code was changed in
    an incompatible way and these buttons are no longer meaningful.

.. _-buildbot-config-directory:

.buildbot config directory
--------------------------

Many of the ``buildbot`` tools must be told how to contact the buildmaster
that they interact with. This specification can be provided as a command-line
argument, but most of the time it will be easier to set them in an "options"
file. The ``buildbot`` command will look for a special directory named
``.buildbot``, starting from the current directory (where the command was run)
and crawling upwards, eventually looking in the user's home directory. It will
look for a file named ``options`` in this directory, and will evaluate it as a
python script, looking for certain names to be set. You can just put simple
``name = 'value'`` pairs in this file to set the options.

For a description of the names used in this file, please see the documentation
for the individual ``buildbot`` sub-commands. The following is a brief sample
of what this file's contents could be. ::

    # for status-reading tools
    masterstatus = 'buildbot.example.org:12345'
    # for 'sendchange' or the debug port
    master = 'buildbot.example.org:18990'
    debugPassword = 'eiv7Po'

Note carefully that the names in the ``options`` file usually do not match the
command-line option name.

:masterstatus: Equivalent to ``--master`` for :ref:`statuslog` and
    :ref:`statusgui`, this gives the location of the
    ``client.PBListener`` status port.

:master: Equivalent to ``--master`` for :ref:`debugclient` and
    :ref:`sendchange`. This option is used for two purposes.  It is
    the location of the ``debugPort`` for ``debugclient`` and the
    location of the ``pb.PBChangeSource`` for ``sendchange``.
    Generally these are the same port.

:debugPassword: Equivalent to ``--passwd`` for :ref:`debugclient`.

    XXX Must match the value of ``c['debugPassword']``, used to protect the
    debug port, for the ``debugclient`` command.

:username: Equivalent to ``--username`` for the :ref:`sendchange`
    command.

:branch: Equivalent to ``--branch`` for the :ref:`sendchange` command.

:category: Equivalent to ``--category`` for the :ref:`sendchange`
    command.

:try_connect: Equivalent to ``--connect``, this specifies how the
    :ref:`try` command should deliver its request to the buildmaster.
    The currently accepted values are "ssh" and "pb".

:try_builders: Equivalent to ``--builders``, specifies which builders
    should be used for the :ref:`try` build.

:try_vc: Equivalent to ``--vc`` for :ref:`try`, this specifies the
    version control system being used.

:try_branch: Equivlanent to ``--branch``, this indicates that the
    current tree is on a non-trunk branch.

:try_topdir:

:try_topfile: Use ``try_topdir``, equivalent to ``--try-topdir``, to
    explicitly indicate the top of your working tree, or
    ``try_topfile``, equivalent to ``--try-topfile`` to name a file
    that will only be found in that top-most directory.

:try_host:

:try_username:

:try_dir: When ``try_connect`` is "ssh", the command will use
    ``try_host`` for ``--tryhost``, ``try_username`` for
    ``--username``, and ``try_dir`` for ``--trydir``.  Apologies for
    the confusing presence and absence of 'try'.

:try_username:

:try_password:

:try_master: Similarly, when ``try_connect`` is "pb", the command will
    pay attention to ``try_username`` for ``--username``,
    ``try_password`` for ``--passwd``, and ``try_master`` for
    ``--master``.

:try_wait:

:masterstatus: ``try_wait`` and ``masterstatus`` (equivalent to
    ``--wait`` and ``master``, respectively) are used to ask the
    :ref:`try` command to wait for the requested build to complete.

buildslave
==========

``buildslave`` command-line tool is used for buildslave management only and
does not provide any additional functionality. One can create, start, stop and
restart the buildslave.

create-slave
------------

This creates a new directory and populates it with files that let it be used
as a buildslave's base directory. You must provide several arguments, which
are used to create the initial ``buildbot.tac`` file.

The ``-r`` option is advisable here, just like for ``create-master``. ::

    buildslave create-slave -r @var{BASEDIR} @var{MASTERHOST}:@var{PORT} @var{SLAVENAME} @var{PASSWORD}

The create-slave options are described in See :ref:`buildslave-options`.

start
-----

This starts a buildslave which was already created in the given base
directory. The daemon is launched in the background, with events logged to a
file named ``twistd.log``. ::

    buildbot start BASEDIR

stop
----

This terminates the daemon buildslave running in the given directory. ::

    buildbot stop BASEDIR