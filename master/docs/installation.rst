Buildbot Components
===================

Buildbot is shipped in two components: the buildmaster (called ``buildbot``
for legacy reasons) and the buildslave.  The buildslave component has far
fewer requirements, and is more broadly compatible than the buildmaster.  You
will need to carefully pick the environment in which to run your buildmaster,
but the buildslave should be able to run just about anywhere.

It is possible to install the buildmaster and buildslave on the same system,
although for anything but the smallest installation this arrangement will not
be very efficient.

Requirements
============

Common Requirements
-------------------

At a bare minimum, you'll need the following for both the buildmaster and a
buildslave:

*   Python: http://www.python.org

    Buildbot requires python-2.4 or later.

*   Twisted: http://twistedmatrix.com

    Both the buildmaster and the buildslaves require Twisted-8.0.x or later.
    As always, the most recent version is recommended.

    Twisted is delivered as a collection of subpackages. You'll need at least
    "Twisted" (the core package), and you'll also want TwistedMail,
    TwistedWeb, and TwistedWords (for sending email, serving a web status
    page, and delivering build status via IRC, respectively). You might also
    want TwistedConch (for the encrypted Manhole debug port). Note that
    Twisted requires ZopeInterface to be installed as well.

Of course, your project's build process will impose additional requirements on
the buildslaves. These hosts must have all the tools necessary to compile and
test your project's source code.

Windows Support
"""""""""""""""

Buildbot - both master and slave - runs well natively on Windows.  The slave
runs well on Cygwin, but because of problems with SQLite on Cygwin, the master
does not.

Buildbot's windows testing is limited to the most recent Twisted and Python
versions.  For best results, use the most recent available versions of these
libraries on Windows.

Note that versions of MSys Git earlier than 1.7.3.1 are known to have problems
with incorrect exit statuses from git commands.  Always use the newest version
of MSys Git.

Buildmaster Requirements
------------------------

*   sqlite3: http://www.sqlite.org

    Buildbot requires SQLite to store its state.  Version 3.3.8 or higher is
    recommended, as earlier versions had trouble with contention for database
    tables.

*   pysqlite: http://pypi.python.org/pypi/pysqlite

    The SQLite Python package is required for python-2.5 and earlier (it is
    already included in python-2.5 and later, but the version in python-2.5
    has nasty bugs)

*   simplejson: http://pypi.python.org/pypi/simplejson

    The simplejson package is required for python-2.5 and earlier (it is
    already included as json in python-2.6 and later)

*   Jinja2: http://jinja.pocoo.org/

    Buildbot requires Jinja version 2.1 or higher.

    Jinja2 is a general purpose templating language and is used by Buildbot to
    generate the HTML output.

*   SQLAlchemy: http://www.sqlalchemy.org/

    Buildbot requires SQLAlchemy 0.6 or higher.  SQLAlchemy allows Buildbot to
    build database schemas and queries for a wide variety of database systems.

*   SQLAlchemy-Migrate: http://code.google.com/p/sqlalchemy-migrate/

    Buildbot requires SQLAlchemy-Migrate version 0.6 (exactly; as-yet
    unreleased later versions may not work).  Buildbot uses SQLAlchemy-Migrate
    to manage schema upgrades from version to version.

.. _installing-the-code:

Installing the code
===================

The Distribution Packages
"""""""""""""""""""""""""

.. index::
    single: Packages
    single: Installation
    single: PyPI

Buildbot comes in two parts: ``buildbot`` (the master) and ``buildbot-slave``
(the slave).  The two can be installed individually or together.

Installation From PyPI
""""""""""""""""""""""

The easiest way to install Buildbot is using ``pip``.  For the master::

    pip install buildbot

and for the slave::

    pip install buildbot-slave

Installation From Tarballs
""""""""""""""""""""""""""

Buildbot and Buildslave can also be installed using the standard python
``distutils`` process. For either component (buildbot or buildbot-slave),
after unpacking the tarball, the process is::

    python setup.py build
    python setup.py install

where the install step may need to be done as root. This will put the bulk of
the code in somewhere like ``/usr/lib/python2.3/site-packages/buildbot``. It
will also install the ``buildbot`` command-line tool in ``/usr/bin/buildbot``.

If the environment variable ``$NO_INSTALL_REQS`` is set to '1', then
``setup.py`` will not try to install Buildbot's requirements.  This is usually
only useful when building a Buildbot package.

To test this, shift to a different directory (like ``/tmp``), and run::

    buildbot --version
    # or
    buildslave --version

If it shows you the versions of Buildbot and Twisted, the install went ok. If
it says ``no such command`` or it gets an ``ImportError`` when it tries to
load the libaries, then something went wrong. ``pydoc buildbot`` is another
useful diagnostic tool.

Windows users will find these files in other places. You will need to make
sure that python can find the libraries, and will probably find it convenient
to have ``buildbot`` on your PATH.

Running Buildbot's Tests (optional)
===================================

If you wish, you can run the buildbot unit test suite.  First, ensure you have
the `mock <http://pypi.python.org/pypi/mock>`_ Python module installed from
PyPi.  This module is not required for ordinary Buildbot operation - only to
run the tests.  Note that this is not the same as the Fedora ``mock`` package!
You can check with ::

    python -mmock

Then, run the tests::

    PYTHONPATH=. trial buildbot.test
    # or
    PYTHONPATH=. trial buildslave.test

Nothing should fail, although a few might be skipped.

If any of the tests fail for reasons other than a missing ``mock``, you should
stop and investigate the cause before continuing the installation process, as
it will probably be easier to track down the bug early.  In most cases, the
problem is incorrectly installed Python modules or a badly configured
PYTHONPATH.  This may be a good time to contact the Buildbot developers for
help.

If you cannot or do not wish to install the buildbot into a site-wide location
like ``/usr`` or ``/usr/local``, you can also install it into the account's
home directory or any other location using a tool like `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_.

Creating a buildmaster
======================

As you learned earlier (see :ref:`system-architecture`), the buildmaster runs
on a central host (usually one that is publically visible, so everybody can
check on the status of the project), and controls all aspects of the buildbot
system.

You will probably wish to create a separate user account for the buildmaster,
perhaps named ``buildmaster``.  Do not run the buildmaster as root!

You also need to choose a directory for the buildmaster, called the
``basedir``. This directory will be owned by the buildmaster.  It will contain
configuration, the adtabase, and status information - including logfiles.  On
a large buildmaster this directory will see a lot of activity, so it should be
on a disk with adequate space and speed.

Once you've picked a basedir, use the ``buildbot create-master`` command to
create the directory and populate it with startup files::

    buildbot create-master -r $basedir

You will need to create a configuration file (see :ref:`configuration`) before
starting the buildmaster. Most of the rest of this manual is dedicated to
explaining how to do this. A sample configuration file is placed in the
working directory, named ``master.cfg.sample``, which can be copied to
``master.cfg`` and edited to suit your purposes.

(Internal details: This command creates a file named ``buildbot.tac`` that
contains all the state necessary to create the buildmaster. Twisted has a tool
called ``twistd`` which can use this .tac file to create and launch a
buildmaster instance. twistd takes care of logging and daemonization (running
the program in the background). ``/usr/bin/buildbot`` is a front end which
runs twistd for you.)

In addition to ``buildbot.tac``, a small ``Makefile.sample`` is installed.
This can be used as the basis for customized daemon startup, See :ref
:`launching-the-daemons`.

Using MySQL
"""""""""""

If you want to use MySQL as the database backend for your Buildbot, add the
``--db`` option to the ``create-master`` invocation to specify the connection
string for the MySQL database (see :ref:`database-specification`), and make
sure that the same URL appears in the ``C['db_url']`` parameter in your
configuration file.

Buildmaster Options
"""""""""""""""""""

This section lists options to the ``create-master`` command. You can also type
``buildslave create-slave --help`` for an up-to-the-moment summary.

:--force: With this option, ``create-master`` will re-use an existing
    master directory.

:--no-logrotate: This disables internal buildslave log management
    mechanism. With this option buildslave does not override the
    default logfile name and its behaviour giving a possibility to
    control those with command-line options of twistd daemon.

:--relocatable: This creates a "relocatable" buildbot.tac, which uses
    relative paths instead of absolute paths, so that the buildmaster
    directory can be moved about.

:--config: The name of the configuration file to use.  This
    configuration file need not reside in the buildmaster directory.

:--log-size: This is the size in bytes when to rotate the Twisted log
    files.  The default is 10MiB.

:--log-count: This is the number of log rotations to keep around. You
    can either specify a number or ``None`` to keep all ``twistd.log``
    files around.  The default is 10.

:--db: The database that the Buildmaster should use.  Note that the
    same value must be added to the configuration file.

Upgrading an Existing Buildmaster
=================================

If you have just installed a new version of the Buildbot code, and you have
buildmasters that were created using an older version, you'll need to upgrade
these buildmasters before you can use them. The upgrade process adds and
modifies files in the buildmaster's base directory to make it compatible with
the new code. ::

    buildbot upgrade-master $BASEDIR

This command will also scan your ``master.cfg`` file for incompatibilities (by
loading it and printing any errors or deprecation warnings that occur). Each
buildbot release tries to be compatible with configurations that worked
cleanly (i.e. without deprecation warnings) on the previous release: any
functions or classes that are to be removed will first be deprecated in a
release, to give you a chance to start using the replacement.

The ``upgrade-master`` command is idempotent. It is safe to run it multiple
times. After each upgrade of the buildbot code, you should use ``upgrade-
master`` on all your buildmasters.

In general, Buildbot slaves and masters can be upgraded independently,
although some new features will not be available, depending on the master and
slave versions.

Beyond this general information, read all of the sections below that apply to
versions through which you are upgrading.

Version-specific Notes
""""""""""""""""""""""

Upgrading a Buildmaster to Buildbot-0.7.6
-----------------------------------------

The 0.7.6 release introduced the ``public_html/`` directory, which contains
``index.html`` and other files served by the ``WebStatus`` and ``Waterfall``
status displays. The ``upgrade-master`` command will create these files if
they do not already exist. It will not modify existing copies, but it will
write a new copy in e.g. ``index.html.new`` if the new version differs from
the version that already exists.

Upgrading a Buildmaster to Buildbot-0.8.0
-----------------------------------------

Buildbot-0.8.0 introduces a database backend, which is SQLite by default.  The
``upgrade-master`` command will automatically create and populate this
database with the changes the buildmaster has seen.  Note that, as of this
release, build history is *not* contained in the database, and is thus not
migrated.

The upgrade process renames the Changes pickle (``$basedir/changes.pck``) to
``changes.pck.old`` once the upgrade is complete.  To reverse the upgrade,
simply downgrade Buildbot and move this file back to its original name.  You
may also wish to delete the state database (``state.sqlite``).

Upgrading into a non-SQLite database
""""""""""""""""""""""""""""""""""""

If you are not using sqlite, you will need to add an entry into your
``master.cfg`` to reflect the database version you are using. The upgrade
process does *not* edit your ``master.cfg`` for you. So something like::

    # for using mysql:
    c['db_url'] = 'mysql://bbuser:<password>@localhost/buildbot'

Once the parameter has been added, invoke ``upgrade-master`` with the ``--db``
parameter, e.g., ::

    buildbot upgrade-master --db=mysql://bbuser:<password>@localhost/buildbot

The ``--db`` option must match the ``c['db_url']`` exactly.

See see :ref:`database-specification` for more options to specify a database.

Change Encoding Issues
""""""""""""""""""""""

The upgrade process assumes that strings in your Changes pickle are encoded in
UTF-8 (or plain ASCII).  If this is not the case, and if there are non-UTF-8
characters in the pickle, the upgrade will fail with a suitable error message.
If this occurs, you have two options.  If the change history is not important
to your purpose, you can simply delete ``changes.pck``.

If you would like to keep the change history, then you will need to figure out
which encoding is in use, and use ``contrib/fix_changes_pickle_encoding.py``
(see :ref:`contrib-scripts`) to rewrite the changes pickle into Unicode before
upgrading the master.  A typical invocation (with Mac-Roman encoding) might
look like::

    $ python $buildbot/contrib/fix_changes_pickle_encoding.py changes.pck macroman
    decoding bytestrings in changes.pck using macroman
    converted 11392 strings
    backing up changes.pck to changes.pck.old

If your Changes pickle uses multiple encodings, you're on your own, but the
script in contrib may provide a good starting point for the fix.

Upgrading a Buildmaster to Later Versions
-----------------------------------------

Up to Buildbot version @value{VERSION}, no further steps beyond those
described above are required.

.. _creating-a-buildslave:

Creating a buildslave
=====================

Typically, you will be adding a buildslave to an existing buildmaster, to
provide additional architecture coverage. The buildbot administrator will give
you several pieces of information necessary to connect to the buildmaster. You
should also be somewhat familiar with the project being tested, so you can
troubleshoot build problems locally.

The buildbot exists to make sure that the project's stated "how to build it"
process actually works. To this end, the buildslave should run in an
environment just like that of your regular developers. Typically the project
build process is documented somewhere (``README``, ``INSTALL``, etc), in a
document that should mention all library dependencies and contain a basic set
of build instructions. This document will be useful as you configure the host
and account in which the buildslave runs.

Here's a good checklist for setting up a buildslave:

#   Set up the account

    It is recommended (although not mandatory) to set up a separate user
    account for the buildslave. This account is frequently named ``buildbot``
    or ``buildslave``. This serves to isolate your personal working
    environment from that of the slave's, and helps to minimize the security
    threat posed by letting possibly-unknown contributors run arbitrary code
    on your system. The account should have a minimum of fancy init scripts.

#   Install the buildbot code

    Follow the instructions given earlier (see :ref:`installing-the-code`). If
    you use a separate buildslave account, and you didn't install the buildbot
    code to a shared location, then you will need to install it with
    ``--home=~`` for each account that needs it.

#   Set up the host

    Make sure the host can actually reach the buildmaster. Usually the
    buildmaster is running a status webserver on the same machine, so simply
    point your web browser at it and see if you can get there. Install
    whatever additional packages or libraries the project's INSTALL document
    advises. (or not: if your buildslave is supposed to make sure that
    building without optional libraries still works, then don't install those
    libraries).

    Again, these libraries don't necessarily have to be installed to a site-
    wide shared location, but they must be available to your build process.
    Accomplishing this is usually very specific to the build process, so
    installing them to ``/usr`` or ``/usr/local`` is usually the best
    approach.

#   Test the build process

    Follow the instructions in the INSTALL document, in the buildslave's
    account. Perform a full CVS (or whatever) checkout, configure, make, run
    tests, etc. Confirm that the build works without manual fussing. If it
    doesn't work when you do it by hand, it will be unlikely to work when the
    buildbot attempts to do it in an automated fashion.

#   Choose a base directory

    This should be somewhere in the buildslave's account, typically named
    after the project which is being tested. The buildslave will not touch any
    file outside of this directory. Something like ``~/Buildbot`` or
    ``~/Buildslaves/fooproject`` is appropriate.

#   Get the buildmaster host/port, botname, and password

    When the buildbot admin configures the buildmaster to accept and use your
    buildslave, they will provide you with the following pieces of
    information:

    *   your buildslave's name

    *   the password assigned to your buildslave

    *   the hostname and port number of the buildmaster, i.e.
        buildbot.example.org:8007

#   Create the buildslave

    Now run the 'buildslave' command as follows::

        buildslave create-slave $BASEDIR $MASTERHOST:$PORT $SLAVENAME $PASSWORD

    This will create the base directory and a collection of files inside,
    including the ``buildbot.tac`` file that contains all the information you
    passed to the ``buildbot`` command.

#   Fill in the hostinfo files

    When it first connects, the buildslave will send a few files up to the
    buildmaster which describe the host that it is running on. These files are
    presented on the web status display so that developers have more
    information to reproduce any test failures that are witnessed by the
    buildbot. There are sample files in the ``info`` subdirectory of the
    buildbot's base directory. You should edit these to correctly describe you
    and your host.

    ``BASEDIR/info/admin`` should contain your name and email address. This is
    the "buildslave admin address", and will be visible from the build status
    page (so you may wish to munge it a bit if address-harvesting spambots are
    a concern).

    ``BASEDIR/info/host`` should be filled with a brief description of the
    host: OS, version, memory size, CPU speed, versions of relevant libraries
    installed, and finally the version of the buildbot code which is running
    the buildslave.

    The optional ``BASEDIR/info/access_uri`` can specify a URI which will
    connect a user to the machine.  Many systems accept ``ssh://hostname``
    URIs for this purpose.

    If you run many buildslaves, you may want to create a single
    ``~buildslave/info`` file and share it among all the buildslaves with
    symlinks.

.. _buildslave-options:

Buildslave Options
------------------

There are a handful of options you might want to use when creating the
buildslave with the ``buildslave create-slave <options> DIR <params>``
command. You can type ``buildslave create-slave --help`` for a summary. To use
these, just include them on the ``buildslave create-slave`` command line, like
this::

    buildslave create-slave --umask=022 ~/buildslave buildmaster.example.org:42012 myslavename mypasswd

:--no-logrotate: This disables internal buildslave log management
    mechanism. With this option buildslave does not override the
    default logfile name and its behaviour giving a possibility to
    control those with command-line options of twistd daemon.

:--usepty: This is a boolean flag that tells the buildslave whether to
    launch child processes in a PTY or with regular pipes (the
    default) when the master does not specify.  This option is
    deprecated, as this particular parameter is better specified on
    the master.

:--umask: This is a string (generally an octal representation of an
    integer) which will cause the buildslave process' "umask" value to
    be set shortly after initialization. The "twistd" daemonization
    utility forces the umask to 077 at startup (which means that all
    files created by the buildslave or its child processes will be
    unreadable by any user other than the buildslave account). If you
    want build products to be readable by other accounts, you can add
    ``--umask=022`` to tell the buildslave to fix the umask after
    twistd clobbers it. If you want build products to be *writable* by
    other accounts too, use ``--umask=000``, but this is likely to be
    a security problem.

:--keepalive: This is a number that indicates how frequently
    "keepalive" messages should be sent from the buildslave to the
    buildmaster, expressed in seconds. The default (600) causes a
    message to be sent to the buildmaster at least once every 10
    minutes. To set this to a lower value, use e.g.
    ``--keepalive=120``.

    If the buildslave is behind a NAT box or stateful firewall, these messages
    may help to keep the connection alive: some NAT boxes tend to forget about
    a connection if it has not been used in a while. When this happens, the
    buildmaster will think that the buildslave has disappeared, and builds
    will time out. Meanwhile the buildslave will not realize than anything is
    wrong.

:--maxdelay: This is a number that indicates the maximum amount of
    time the buildslave will wait between connection attempts,
    expressed in seconds. The default (300) causes the buildslave to
    wait at most 5 minutes before trying to connect to the buildmaster
    again.

:--log-size: This is the size in bytes when to rotate the Twisted log
    files.  The default is 10MiB.

:--log-count: This is the number of log rotations to keep around. You
    can either specify a number or ``None`` to keep all ``twistd.log``
    files around.  The default is 10.

Other Buildslave Configuration
------------------------------

:unicode_encoding: This represents the encoding that buildbot should
    use when converting unicode commandline arguments into byte
    strings in order to pass to the operating system when spawning new
    processes.

    The default value is what python's sys.getfilesystemencoding() returns,
    which on Windows is 'mbcs', on Mac OSX is 'utf-8', and on Unix depends on
    your locale settings.

    If you need a different encoding, this can be changed in your build
    slave's buildbot.tac file by adding a unicode_encoding argument to the
    BuildSlave constructor.

:allow_shutdown: allow_shutdown can be passed to the BuildSlave
    constructor in buildbot.tac.  If set, it allows the buildslave to
    initiate a graceful shutdown, meaning that it will ask the master
    to shut down the slave when the current build, if any, is
    complete.

    Setting allow_shutdown to 'file' will cause the buildslave to watch
    'shutdown.stamp' in basedir for updates to its mtime.  When the mtime
    changes, the slave will request a graceful shutdown from the master.  The
    file does not need to exist prior to starting the slave.

    Setting allow_shutdown to 'signal' will set up a SIGHUP handler to start a
    graceful shutdown.  When the signal is received, the slave will request a
    graceful shutdown from the master.

    The default value is None, in which case this feature will be disabled.

    Both master and slave must be at least version 0.8.3 for this feature to
    work. ::

        s = BuildSlave(buildmaster_host, port, slavename, passwd, basedir,
                       keepalive, usepty, umask=umask, maxdelay=maxdelay,
                       unicode_encoding='utf-8', allow_shutdown='signal')

Upgrading an Existing Buildslave
================================

If you have just installed a new version of Buildbot-slave, you may need to
take some steps to upgrade it.  If you are upgrading to version 0.8.2 or
later, you can run ::

    buildslave upgrade-slave /path/to/buildslave/dir

Version-specific Notes
""""""""""""""""""""""

Upgrading a Buildslave to Buildbot-slave-0.8.1
----------------------------------------------

Before Buildbot version 0.8.1, the Buildbot master and slave were part of the
same distribution.  As of version 0.8.1, the buildslave is a separate
distribution.

As of this release, you will need to install *buildbot-slave* to run a slave.

Any automatic startup scripts that had run ``buildbot start`` for previous
versions should be changed to run ``buildslave start`` instead.

If you are running a version later than 0.8.1, then you can skip the remainder
of this section: the ``upgrade-slave`` command will take care of this.  If you
are upgrading directly to 0.8.1, read on.

The existing ``buildbot.tac`` for any buildslaves running older versions will
need to be edited or replaced.  If the loss of cached buildslave state (e.g.,
for Source steps in copy mode) is not problematic, the easiest solution is to
simply delete the slave directory and re-run ``buildslave create-slave``.

If deleting the slave directory is problematic, the change to ``buildbot.tac``
is simple.  On line 3, replace ::

    from buildbot.slave.bot import BuildSlave

with ::

    from buildslave.bot import BuildSlave

After this change, the buildslave should start as usual.

.. _launching-the-daemons:

Launching the daemons
=====================

Both the buildmaster and the buildslave run as daemon programs. To launch
them, pass the working directory to the ``buildbot`` and ``buildslave``
commands, as appropriate::

    # start a master
    buildbot start $BASEDIR
    # start a slave
    buildslave start $SLAVE_BASEDIR

The ``BASEDIR`` is option and can be omitted if the current directory contains
the buildbot configuration (the ``buildbot.tac`` file). ::

    buildbot start

This command will start the daemon and then return, so normally it will not
produce any output. To verify that the programs are indeed running, look for a
pair of files named ``twistd.log`` and ``twistd.pid`` that should be created
in the working directory. ``twistd.pid`` contains the process ID of the newly-
spawned daemon.

When the buildslave connects to the buildmaster, new directories will start
appearing in its base directory. The buildmaster tells the slave to create a
directory for each Builder which will be using that slave. All build
operations are performed within these directories: CVS checkouts, compiles,
and tests.

Once you get everything running, you will want to arrange for the buildbot
daemons to be started at boot time. One way is to use ``cron``, by putting
them in a @reboot crontab entry [1]_::

    @reboot buildbot start $BASEDIR

When you run ``crontab`` to set this up, remember to do it as the buildmaster
or buildslave account! If you add this to your crontab when running as your
regular account (or worse yet, root), then the daemon will run as the wrong
user, quite possibly as one with more authority than you intended to provide.

It is important to remember that the environment provided to cron jobs and
init scripts can be quite different that your normal runtime. There may be
fewer environment variables specified, and the PATH may be shorter than usual.
It is a good idea to test out this method of launching the buildslave by using
a cron job with a time in the near future, with the same command, and then
check ``twistd.log`` to make sure the slave actually started correctly. Common
problems here are for ``/usr/local`` or ``~/bin`` to not be on your ``PATH``,
or for ``PYTHONPATH`` to not be set correctly. Sometimes ``HOME`` is messed up
too.

Some distributions may include conveniences to make starting buildbot at boot
time easy.  For instance, with the default buildbot package in Debian-based
distributions, you may only need to modify ``/etc/default/buildbot`` (see also
``/etc/init.d/buildbot``, which reads the configuration in
``/etc/default/buildbot``).

Buildbot also comes with its own init scripts that provide support for
controlling multi-slave and multi-master setups (mostly because they are based
on the init script from the debian package).  With a little modification these
scripts can be used both on debian and rhel based distributions and may thus
prove helpful to package maintainers who are working on buildbot (or those
that haven't yet split buildbot into master and slave packages). ::

    # install as /etc/default|sysconfig/buildslave
    master/contrib/init-scripts/buildslave.default

    # install /etc/default|sysconfig/buildslave
    master/contrib/init-scripts/buildmaster.default

    # install as /etc/init.d/buildslave
    slave/contrib/init-scripts/buildslave.init.sh

    # install as /etc/init.d/buildmaster
    slave/contrib/init-scripts/buildmaster.init.sh

    # ... and tell sysvinit about them
    chkconfig buildmaster reset
    # ... or
    update-rc.d buildmaster defaults

.. _logfiles:

Logfiles
========

.. index::
    single: logfiles

While a buildbot daemon runs, it emits text to a logfile, named
``twistd.log``. A command like ``tail -f twistd.log`` is useful to watch the
command output as it runs.

The buildmaster will announce any errors with its configuration file in the
logfile, so it is a good idea to look at the log at startup time to check for
any problems. Most buildmaster activities will cause lines to be added to the
log.

Shutdown
========

To stop a buildmaster or buildslave manually, use::

    buildbot stop $BASEDIR
    # or
    buildslave stop $SLAVE_BASEDIR

This simply looks for the ``twistd.pid`` file and kills whatever process is
identified within.

At system shutdown, all processes are sent a ``SIGKILL``. The buildmaster and
buildslave will respond to this by shutting down normally.

The buildmaster will respond to a ``SIGHUP`` by re-reading its config file. Of
course, this only works on unix-like systems with signal support, and won't
work on Windows. The following shortcut is available::

    buildbot reconfig $BASEDIR

When you update the Buildbot code to a new release, you will need to restart
the buildmaster and/or buildslave before it can take advantage of the new
code. You can do a ``buildbot stop $BASEDIR`` and ``buildbot start $BASEDIR``
in quick succession, or you can use the ``restart`` shortcut, which does both
steps for you::

    buildbot restart $BASEDIR

Buildslaves can similarly be restarted with::

    buildslave restart $BASEDIR

There are certain configuration changes that are not handled cleanly by
``buildbot reconfig``. If this occurs, ``buildbot restart`` is a more robust
tool to fully switch over to the new configuration.

``buildbot restart`` may also be used to start a stopped Buildbot instance.
This behaviour is useful when writing scripts that stop, start and restart
Buildbot.

A buildslave may also be gracefully shutdown from the see :ref:`webstatus`
status plugin. This is useful to shutdown a buildslave without interrupting
any current builds. The buildmaster will wait until the buildslave is finished
all its current builds, and will then tell the buildslave to shutdown.

Maintenance
===========

The buildmaster can be configured to send out email notifications when a slave
has been offline for a while.  Be sure to configure the buildmaster with a
contact email address for each slave so these notifications are sent to
someone who can bring it back online.

If you find you can no longer provide a buildslave to the project, please let
the project admins know, so they can put out a call for a replacement.

The Buildbot records status and logs output continually, each time a build is
performed. The status tends to be small, but the build logs can become quite
large. Each build and log are recorded in a separate file, arranged
hierarchically under the buildmaster's base directory. To prevent these files
from growing without bound, you should periodically delete old build logs. A
simple cron job to delete anything older than, say, two weeks should do the
job. The only trick is to leave the ``buildbot.tac`` and other support files
alone, for which find's ``-mindepth`` argument helps skip everything in the
top directory. You can use something like the following::

    @weekly cd BASEDIR && find . -mindepth 2 -ipath './public_html/*' -prune -o -type f -mtime +14 -exec rm {} \;
    @weekly cd BASEDIR && find twistd.log* -mtime +14 -exec rm {} \;

Alternatively, you can configure a maximum number of old logs to be kept using
the ``--log-count`` command line option when running ``buildbot create-slave``
or ``buildbot create-master``.

Troubleshooting
===============

Here are a few hints on diagnosing common problems.

Starting the buildslave
-----------------------

Cron jobs are typically run with a minimal shell (``/bin/sh``, not
``/bin/bash``), and tilde expansion is not always performed in such commands.
You may want to use explicit paths, because the ``PATH`` is usually quite
short and doesn't include anything set by your shell's startup scripts
(``.profile``, ``.bashrc``, etc). If you've installed buildbot (or other
python libraries) to an unusual location, you may need to add a ``PYTHONPATH``
specification (note that python will do tilde-expansion on ``PYTHONPATH``
elements by itself). Sometimes it is safer to fully-specify everything::

    @reboot PYTHONPATH=~/lib/python /usr/local/bin/buildbot start /usr/home/buildbot/basedir

Take the time to get the @reboot job set up. Otherwise, things will work fine
for a while, but the first power outage or system reboot you have will stop
the buildslave with nothing but the cries of sorrowful developers to remind
you that it has gone away.

Connecting to the buildmaster
-----------------------------

If the buildslave cannot connect to the buildmaster, the reason should be
described in the ``twistd.log`` logfile. Some common problems are an incorrect
master hostname or port number, or a mistyped bot name or password. If the
buildslave loses the connection to the master, it is supposed to attempt to
reconnect with an exponentially-increasing backoff. Each attempt (and the time
of the next attempt) will be logged. If you get impatient, just manually stop
and re-start the buildslave.

When the buildmaster is restarted, all slaves will be disconnected, and will
attempt to reconnect as usual. The reconnect time will depend upon how long
the buildmaster is offline (i.e. how far up the exponential backoff curve the
slaves have travelled). Again, ``buildslave restart $BASEDIR`` will speed up
the process.

.. _contrib-scripts:

Contrib Scripts
===============

While some features of Buildbot are included in the distribution, others are
only available in ``contrib/`` in the source directory.  The latest versions
of such scripts are available at
http://github.com/buildbot/buildbot/tree/master/master/contrib.

.. rubric:: footnotes

.. [1] this @reboot syntax is understood by Vixie cron, which is the flavor
   usually provided with linux systems. Other unices may have a cron that
   doesn't understand @reboot
