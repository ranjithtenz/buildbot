Schedulers are responsible for initiating builds on builders.

Some schedulers listen for changes from ChangeSources and generate build sets
in response to these changes.  Others generate build sets without changes,
based on other events in the buildmaster.

.. _configuring-schedulers:

Configuring Schedulers
----------------------

.. index::
    single: c['schedulers']

``c['schedulers']`` is a list of Scheduler instances, each of which causes
builds to be started on a particular set of Builders. The two basic Scheduler
classes you are likely to start with are ``Scheduler`` and ``Periodic``, but
you can write a customized subclass to implement more complicated build
scheduling.

Scheduler arguments should always be specified by name (as keyword arguments),
to allow for future expansion::

    sched = Scheduler(name="quick", builderNames=['lin', 'win'])

There are several common arguments for schedulers, although not all are
available with all schedulers.

.. index::
    single: Properties

:name:

    Each Scheduler must have a unique name. This is used in status displays,
    and is also available in the build property ``scheduler``.

:builderNames:

    This is the set of builders which this scheduler should trigger, specified
    as a list of names (strings).

:properties:

    This is a dictionary specifying properties that will be transmitted to all
    builds started by this scheduler.  The ``owner`` property may be of
    particular interest, as its contents (as a list) will be added to the list
    of "interested users" (see :ref:`doing-things-with-users`) for each
    triggered build. For example::

        sched = Scheduler(...,
            properties = { 'owner' : [ 'zorro@company.com', 'silver@company.com' ] })

:fileIsImportant: A callable which takes one argument, a Change
    instance, and returns ``True`` if the change is worth building,
    and ``False`` if it is not.  Unimportant Changes are accumulated
    until the build is triggered by an important change.  The default
    value of None means that all Changes are important.

:change_filter: The change filter that will determine which changes
    are recognized by this scheduler; see :ref:`change-filters`.  Note
    that this is different from ``fileIsImportant``: if the change
    filter filters out a Change, then it is completely ignored by the
    scheduler.  If a Change is allowed by the change filter, but is
    deemed unimportant, then it will not cause builds to start, but
    will be remembered and shown in status displays.

The remaining subsections represent a catalog of the available Scheduler
types. All these Schedulers are defined in modules under
``buildbot.schedulers``, and the docstrings there are the best source of
documentation on the arguments taken by each one.

.. _change-filters:

Change Filters
--------------

.. index::
    single: buildbot.schedulers.filter.ChangeFilter

Several schedulers perform filtering on an incoming set of changes.  The
filter can most generically be specified as a ChangeFilter.  Set up a
ChangeFilter like this::

    from buildbot.changes.filter import ChangeFilter
    my_filter = ChangeFilter(
        project_re="^baseproduct/.*",
        branch="devel")

and then add it to a scheduler with the ``change_filter`` parameter::

    sch = SomeSchedulerClass(...,
        change_filter=my_filter)

There are four attributes of changes on which you can filter:

:@code{project}: the project string, as defined by the ChangeSource.

:@code{repository}: the repository in which this change occurred.

:@code{branch}: the branch on which this change occurred.  Note that
    'trunk' or 'master' is often denoted by ``None``.

:@code{category}: the category, again as defined by the ChangeSource.

For each attribute, the filter can look for a single, specific value::

    my_filter = ChangeFilter(project = 'myproject')

or accept any of a set of values::

    my_filter = ChangeFilter(project = ['myproject', 'jimsproject'])

It can apply a regular expression, use the attribute name with a suffix of
``_re``::

    my_filter = ChangeFilter(category_re = '.*deve.*')
    # or, to use regular expression flags:
    import re
    my_filter = ChangeFilter(category_re = re.compile('.*deve.*', re.I))

For anything more complicated, define a Python function to recognize the
strings you want::

    def my_branch_fn(branch):
        return branch in branches_to_build and branch not in branches_to_ignore
    my_filter = ChangeFilter(branch_fn = my_branch_fn)

The special argument ``filter_fn`` can be used to specify a function that is
given the entire Change object, and returns a boolean.

A Change passes the filter only if *all* arguments are satisfied.  If no
filter object is given to a scheduler, then all changes will be built (subject
to any other restrictions the scheduler enforces).

SingleBranchScheduler
---------------------

.. index::
    single: buildbot.schedulers.basic.SingleBranchScheduler

This is the original and still most popular scheduler class. It follows
exactly one branch, and starts a configurable tree-stable-timer after each
change on that branch. When the timer expires, it starts a build on some set
of Builders. The scheduler accepts a ``fileIsImportant`` function which can be
used to ignore some Changes if they do not affect any "important" files.

The arguments to this scheduler are:

:name:

:builderNames:

:properties:

:fileIsImportant:

:change_filter: See :ref:`configuring-schedulers`

:treeStableTimer: The scheduler will wait for this many seconds before
    starting the build. If new changes are made during this interval,
    the timer will be restarted, so really the build will be started
    after a change and then after this many seconds of inactivity.

    If treeStableTimer is ``None``, then a separate build is started
    immediately for each Change.

:categories (deprecated; use change_filter): A list of categories of
    changes that this scheduler will respond to.  If this is
    specified, then any non-matching changes are ignored.

:branch (deprecated; use change_filter): The scheduler will pay
    attention to this branch, ignoring Changes that occur on other
    branches. Setting ``branch`` equal to the special value of
    ``None`` means it should only pay attention to the default branch.
    Note that ``None`` is a keyword, not a string, so write ``None``
    and not ``"None"``.

Example::

    from buildbot.schedulers.basic  import SingleBranchScheduler
    quick = SingleBranchScheduler(name="quick",
                        branch=None,
                        treeStableTimer=60,
                        builderNames=["quick-linux", "quick-netbsd"])
    full = SingleBranchScheduler(name="full",
                        branch=None,
                        treeStableTimer=5*60,
                        builderNames=["full-linux", "full-netbsd", "full-OSX"])
    c['schedulers'] = [quick, full]

In this example, the two "quick" builders are triggered 60 seconds after the
tree has been changed. The "full" builds do not run quite so quickly (they
wait 5 minutes), so hopefully if the quick builds fail due to a missing file
or really simple typo, the developer can discover and fix the problem before
the full builds are started. Both Schedulers only pay attention to the default
branch: any changes on other branches are ignored by these schedulers. Each
scheduler triggers a different set of Builders, referenced by name.

.. index::
    single: buildbot.schedulers.basic.Scheduler
    single: buildbot.scheduler.Scheduler

The old names for this scheduler, ``buildbot.scheduler.Scheduler`` and
``buildbot.schedulers.basic.Scheduler``, are deprecated in favor of the more
accurate name ``SingleBranchScheduler``.

AnyBranchScheduler
------------------

.. index::
    single: buildbot.schedulers.basic.AnyBranchScheduler

This scheduler uses a tree-stable-timer like the default one, but uses a
separate timer for each branch.

The arguments to this scheduler are:

:name:

:builderNames:

:properties:

:fileIsImportant:

:change_filter: See :ref:`configuring-schedulers`

:treeStableTimer: The scheduler will wait for this many seconds before
    starting the build. If new changes are made during this interval,
    the timer will be restarted, so really the build will be started
    after a change and then after this many seconds of inactivity.

:branches (deprecated; use change_filter): This scheduler will pay
    attention to any number of branches, ignoring Changes that occur
    on other branches.

:categories (deprecated; use change_filter): A list of categories of
    changes that this scheduler will respond to.  If this is
    specified, then any non-matching changes are ignored.

Dependent Scheduler
-------------------

.. index::
    single: Dependent
    single: Dependencies
    single: buildbot.schedulers.dependent.Dependent
    single: buildbot.schedulers.basic.Dependent

It is common to wind up with one kind of build which should only be performed
if the same source code was successfully handled by some other kind of build
first. An example might be a packaging step: you might only want to produce
.deb or RPM packages from a tree that was known to compile successfully and
pass all unit tests. You could put the packaging step in the same Build as the
compile and testing steps, but there might be other reasons to not do this (in
particular you might have several Builders worth of compiles/tests, but only
wish to do the packaging once). Another example is if you want to skip the
"full" builds after a failing "quick" build of the same source code. Or, if
one Build creates a product (like a compiled library) that is used by some
other Builder, you'd want to make sure the consuming Build is run *after* the
producing one.

You can use "Dependencies" to express this relationship to the Buildbot. There
is a special kind of scheduler named ``scheduler.Dependent`` that will watch
an "upstream" scheduler for builds to complete successfully (on all of its
Builders). Each time that happens, the same source code (i.e. the same
``SourceStamp``) will be used to start a new set of builds, on a different set
of Builders. This "downstream" scheduler doesn't pay attention to Changes at
all. It only pays attention to the upstream scheduler.

If the build fails on any of the Builders in the upstream set, the downstream
builds will not fire.  Note that, for SourceStamps generated by a
ChangeSource, the ``revision`` is None, meaning HEAD. If any changes are
committed between the time the upstream scheduler begins its build and the
time the dependent scheduler begins its build, then those changes will be
included in the downstream build. See the see :ref:`triggerable-scheduler` for
a more flexible dependency mechanism that can avoid this problem.

The keyword arguments to this scheduler are:

:name:

:builderNames:

:properties:

:upstream: The upstream scheduler to watch.  Note that this is an
    "instance", not the name of the scheduler.

Example::

    from buildbot.schedulers import dependent
    tests = basic.SingleBranchScheduler(name="just-tests", branch=None,
                    treeStableTimer=5*60,
                    builderNames=["full-linux", "full-netbsd", "full-OSX"])
    package = dependent.Dependent(name="build-package",
                    upstream=tests, # <- no quotes!
                    builderNames=["make-tarball", "make-deb", "make-rpm"])
    c['schedulers'] = [tests, package]

Periodic Scheduler
------------------

.. index::
    single: buildbot.schedulers.timed.Periodic

This simple scheduler just triggers a build every N seconds.

The arguments to this scheduler are:

:name:

:builderNames:

:properties:

:periodicBuildTimer: The time, in seconds, after which to start a
    build.

Example::

    from buildbot.schedulers import timed
    nightly = timed.Periodic(name="daily",
                    builderNames=["full-solaris"],
                    periodicBuildTimer=24*60*60)
    c['schedulers'] = [nightly]

The scheduler in this example just runs the full solaris build once per day.
Note that this scheduler only lets you control the time between builds, not
the absolute time-of-day of each Build, so this could easily wind up an
"evening" or "every afternoon" scheduler depending upon when it was first
activated.

Nightly Scheduler
-----------------

.. index::
    single: buildbot.schedulers.timed.Nightly

This is highly configurable periodic build scheduler, which triggers a build
at particular times of day, week, month, or year. The configuration syntax is
very similar to the well-known ``crontab`` format, in which you provide values
for minute, hour, day, and month (some of which can be wildcards), and a build
is triggered whenever the current time matches the given constraints. This can
run a build every night, every morning, every weekend, alternate Thursdays, on
your boss's birthday, etc.

Pass some subset of ``minute``, ``hour``, ``dayOfMonth``, ``month``, and
``dayOfWeek``; each may be a single number or a list of valid values. The
builds will be triggered whenever the current time matches these values.
Wildcards are represented by a '*' string. All fields default to a wildcard
except 'minute', so with no fields this defaults to a build every hour, on the
hour. The full list of parameters is:

:name:

:builderNames:

:properties:

:fileIsImportant:

:branch: (required) The branch to build when the time comes.  Remember
    that a value of ``None`` here means the default branch, and will
    not match other branches!

:change_filter: See :ref:`configuring-schedulers`.  Note that
    ``fileIsImportant`` and ``change_filter`` are only relevant if
    ``onlyIfChanged`` is true.

:minute: The minute of the hour on which to start the build.  This
    defaults to 0, meaning an hourly build.

:hour: The hour of the day on which to start the build, in 24-hour
    notation. This defaults to ``*``, meaning every hour.

:dayOfMonth: The day of the month to start a build.  This defauls to
    ``*``, meaning every day.

:month: The month in which to start the build, with January = 1.  This
    defaults to *, meaning every month.

:dayOfWeek: The day of the week to start a build, with Monday = 0.
    This defaults to ``*``, meaning every day of the week.  If
    ``dayOfMonth`` and ``dayOfWeek`` are both specified, builds will
    be started when *either* parameter matches.

:onlyIfChanged: If this is true, then builds will not be scheduled at
    the designated time *unless* the specified branch has seen an
    important change since the previous build.

For example, the following master.cfg clause will cause a build to be started
every night at 3:00am::

    from buildbot.schedulers import timed
    s = timed.Nightly(name='nightly',
            branch='master',
            builderNames=['builder1', 'builder2'],
            hour=3,
            minute=0)

This scheduler will perform a build each monday morning at 6:23am and again at
8:23am, but only if someone has committed code in the interim::

    s = timed.Nightly(name='BeforeWork',
             branch='default',
             builderNames=['builder1'],
             dayOfWeek=0,
             hour=[6,8],
             minute=23,
             onlyIfChanged=True)

The following runs a build every two hours, using Python's ``range`` function::

    s = timed.Nightly(name='every2hours',
            branch=None, # default branch
            builderNames=['builder1'],
            hour=range(0, 24, 2))

Finally, this example will run only on December 24th::

    s = timed.Nightly(name='SleighPreflightCheck',
            branch=None, # default branch
            builderNames=['flying_circuits', 'radar'],
            month=12,
            dayOfMonth=24,
            hour=12,
            minute=0)

.. _try-schedulers:

Try Schedulers
--------------

.. index::
    single: buildbot.schedulers.trysched.Try_Jobdir
    single: buildbot.schedulers.trysched.Try_Userpass

This scheduler allows developers to use the ``buildbot try`` command to
trigger builds of code they have not yet committed. See :ref:`try` for
complete details.

Two implementations are available: ``Try_Jobdir`` and ``Try_Userpass``.  The
former monitors a job directory, specified by the ``jobdir`` parameter, while
the latter listens for PB connections on a specific ``port``, and
authenticates against ``userport``.

The buildmaster must have a scheduler instance in the config file's
``c['schedulers']`` list to receive try requests. This lets the administrator
control who may initiate these "trial" builds, which branches are eligible for
trial builds, and which Builders should be used for them.

The scheduler has various means to accept build requests. All of them enforce
more security than the usual buildmaster ports do. Any source code being built
can be used to compromise the buildslave accounts, but in general that code
must be checked out from the VC repository first, so only people with commit
privileges can get control of the buildslaves. The usual force-build control
channels can waste buildslave time but do not allow arbitrary commands to be
executed by people who don't have those commit privileges. However, the source
code patch that is provided with the trial build does not have to go through
the VC system first, so it is important to make sure these builds cannot be
abused by a non-committer to acquire as much control over the buildslaves as a
committer has. Ideally, only developers who have commit access to the VC
repository would be able to start trial builds, but unfortunately the
buildmaster does not, in general, have access to VC system's user list.

As a result, the try scheduler requires a bit more configuration. There are
currently two ways to set this up:

:jobdir (ssh):

    This approach creates a command queue directory, called the "jobdir", in
    the buildmaster's working directory. The buildmaster admin sets the
    ownership and permissions of this directory to only grant write access to
    the desired set of developers, all of whom must have accounts on the
    machine. The ``buildbot try`` command creates a special file containing
    the source stamp information and drops it in the jobdir, just like a
    standard maildir. When the buildmaster notices the new file, it unpacks
    the information inside and starts the builds.

    The config file entries used by 'buildbot try' either specify a local
    queuedir (for which write and mv are used) or a remote one (using scp and
    ssh).

    The advantage of this scheme is that it is quite secure, the disadvantage
    is that it requires fiddling outside the buildmaster config (to set the
    permissions on the jobdir correctly). If the buildmaster machine happens
    to also house the VC repository, then it can be fairly easy to keep the VC
    userlist in sync with the trial-build userlist. If they are on different
    machines, this will be much more of a hassle. It may also involve granting
    developer accounts on a machine that would not otherwise require them.

    To implement this, the buildslave invokes 'ssh -l username host buildbot
    tryserver ARGS', passing the patch contents over stdin. The arguments must
    include the inlet directory and the revision information.

:user+password (PB):

    In this approach, each developer gets a username/password pair, which are
    all listed in the buildmaster's configuration file. When the developer
    runs ``buildbot try``, their machine connects to the buildmaster via PB
    and authenticates themselves using that username and password, then sends
    a PB command to start the trial build.

    The advantage of this scheme is that the entire configuration is performed
    inside the buildmaster's config file. The disadvantages are that it is
    less secure (while the "cred" authentication system does not expose the
    password in plaintext over the wire, it does not offer most of the other
    security properties that SSH does). In addition, the buildmaster admin is
    responsible for maintaining the username/password list, adding and
    deleting entries as developers come and go.

For example, to set up the "jobdir" style of trial build, using a command
queue directory of ``MASTERDIR/jobdir`` (and assuming that all your project
developers were members of the ``developers`` unix group), you would first set
up that directory::

    mkdir -p MASTERDIR/jobdir MASTERDIR/jobdir/new MASTERDIR/jobdir/cur MASTERDIR/jobdir/tmp
    chgrp developers MASTERDIR/jobdir MASTERDIR/jobdir/*
    chmod g+rwx,o-rwx MASTERDIR/jobdir MASTERDIR/jobdir/*

and then use the following scheduler in the buildmaster's config file::

    from buildbot.schedulers.trysched import Try_Jobdir
    s = Try_Jobdir(name="try1",
                   builderNames=["full-linux", "full-netbsd", "full-OSX"],
                   jobdir="jobdir")
    c['schedulers'] = [s]

Note that you must create the jobdir before telling the buildmaster to use
this configuration, otherwise you will get an error. Also remember that the
buildmaster must be able to read and write to the jobdir as well. Be sure to
watch the ``twistd.log`` file (see :ref:`logfiles`) as you start using the
jobdir, to make sure the buildmaster is happy with it.

To use the username/password form of authentication, create a ``Try_Userpass``
instance instead. It takes the same ``builderNames`` argument as the
``Try_Jobdir`` form, but accepts an addtional ``port`` argument (to specify
the TCP port to listen on) and a ``userpass`` list of username/password pairs
to accept. Remember to use good passwords for this: the security of the
buildslave accounts depends upon it::

    from buildbot.schedulers.trysched import Try_Userpass
    s = Try_Userpass(name="try2",
                     builderNames=["full-linux", "full-netbsd", "full-OSX"],
                     port=8031,
                     userpass=[("alice","pw1"), ("bob", "pw2")] )
    c['schedulers'] = [s]

Like most places in the buildbot, the ``port`` argument takes a strports
specification. See ``twisted.application.strports`` for details.

.. _triggerable-scheduler:

Triggerable Scheduler
---------------------

.. index::
    single: Triggers
    single: buildbot.schedulers.triggerable.Triggerable

The ``Triggerable`` scheduler waits to be triggered by a Trigger step (see
:ref:`triggering-schedulers`) in another build. That step can optionally wait
for the scheduler's builds to complete. This provides two advantages over
Dependent schedulers. First, the same scheduler can be triggered from multiple
builds. Second, the ability to wait for a Triggerable's builds to complete
provides a form of "subroutine call", where one or more builds can "call" a
scheduler to perform some work for them, perhaps on other buildslaves.

The parameters are just the basics:

:name:

:builderNames:

:properties:

This class is only useful in conjunction with the ``Trigger`` step. Here is a
fully-worked example::

    from buildbot.schedulers import basic, timed, triggerable
    from buildbot.process import factory
    from buildbot.steps import trigger

    checkin = basic.SingleBranchScheduler(name="checkin",
                branch=None,
                treeStableTimer=5*60,
                builderNames=["checkin"])
    nightly = timed.Nightly(name='nightly',
                builderNames=['nightly'],
                hour=3,
                minute=0)

    mktarball = triggerable.Triggerable(name="mktarball",
                    builderNames=["mktarball"])
    build = triggerable.Triggerable(name="build-all-platforms",
                    builderNames=["build-all-platforms"])
    test = triggerable.Triggerable(name="distributed-test",
                    builderNames=["distributed-test"])
    package = triggerable.Triggerable(name="package-all-platforms",
                    builderNames=["package-all-platforms"])

    c['schedulers'] = [mktarball, checkin, nightly, build, test, package]

    # on checkin, make a tarball, build it, and test it
    checkin_factory = factory.BuildFactory()
    checkin_factory.addStep(trigger.Trigger(schedulerNames=['mktarball'],
                                           waitForFinish=True))
    checkin_factory.addStep(trigger.Trigger(schedulerNames=['build-all-platforms'],
                                       waitForFinish=True))
    checkin_factory.addStep(trigger.Trigger(schedulerNames=['distributed-test'],
                                      waitForFinish=True))

    # and every night, make a tarball, build it, and package it
    nightly_factory = factory.BuildFactory()
    nightly_factory.addStep(trigger.Trigger(schedulerNames=['mktarball'],
                                           waitForFinish=True))
    nightly_factory.addStep(trigger.Trigger(schedulerNames=['build-all-platforms'],
                                       waitForFinish=True))
    nightly_factory.addStep(trigger.Trigger(schedulerNames=['package-all-platforms'],
                                         waitForFinish=True))

Scheduler Index
---------------

@printindex sl