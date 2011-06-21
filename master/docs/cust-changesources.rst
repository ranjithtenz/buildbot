For some version-control systems, making Bulidbot aware of new changes can be
a challenge.  If the pre-supplied classes in see :ref:`change-sources` are not
sufficient, then you will need to write your own.

There are three approaches, one of which is not even a change source. The
first option is to write a change source that exposes some service to which
the version control system can "push" changes.  This can be more complicated,
since it requires implementing a new service, but delivers changes to Buildbot
immediately on commit.

The second option is often preferable to the first: implement a notification
service in an external process (perhaps one that is started directly by the
version control system, or by an email server) and delivers changes to
Buildbot via see :ref:`pbchangesource`.  This section does not describe this
particular approach, since it requires no customization within the buildmaster
process.

The third option is to write a change source which polls for changes -
repeatedly connecting to an external service to check for new changes.  This
works well in many cases, but can produce a high load on the version control
system if polling is too frequent, and can take too long to notice changes if
the polling is not frequent enough.

Writing a Change Source
-----------------------

.. index::
    single: buildbot.changes.base.ChangeSource

A custom change source must implement ``buildbot.interfaces.IChangeSource``.

The easiest way to do this is to subclass
``buildbot.changes.base.ChangeSource``, implementing the ``describe`` method
to describe the instance.  ``ChangeSource`` is a Twisted service, so you will
need to implement the ``startService`` and ``stopService`` methods to control
the means by which your change source receives notifications.

When the class does receive a change, it should call
``self.master.addChange(..)`` to submit it to the buildmaster.  This method
shares the same parameters as ``master.db.changes.addChange``, so consult the
API documentation for that function for details on the available arguments.

You will probably also want to set ``compare_attrs`` to the list of object
attributes which Buildbot will use to compare one change source to another
when reconfiguring.  During reconfiguration, if the new change source is
different from the old, then the old will be stopped and the new started.

Writing a Change Poller
-----------------------

.. index::
    single: buildbot.changes.base.PollingChangeSource

Polling is a very common means of seeking changes, so Buildbot supplies a
utility parent class to make it easier.  A poller should subclass
``buildbot.changes.base.PollingChangeSource``, which is a subclass of
``ChangeSource``.  This subclass implements the ``Service`` methods, and
causes the ``poll`` method to be called every ``self.pollInterval`` seconds.
This method should return a Deferred to signal its completion.

Aside from the service methods, the other concerns in the previous section
apply here, too.