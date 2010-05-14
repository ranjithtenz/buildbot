import time

from twisted.trial import unittest

from buildbot.changes import changes

class Change(unittest.TestCase):
    def assertEqualUnicode(self, x, y, msg=None):
        if not isinstance(x, unicode):
            self.fail("%r is not unicode" % (x,))
        self.assertEqual(x, y, msg)

    def getBigChange(self):
        return changes.Change(u'me', [ u'foo.c' ], u'fixes',
                isdir=1, links=['http://buildbot.net'],
                revision=u'456', when=1273727073, branch=u'branches/release',
                category=u'important', revlink=u'http://buildbot.net',
                properties={'foo':'bar'}, repository=u'http://svn.buildbot.net',
                project=u'buildbot')

    # --

    def test_constructor_minimal(self):
        c = changes.Change(u'djmitche', [ u'changes.py' ], u'I hate this file')
        self.assertEqual(
                [ c.who, c.files, c.comments,
                  c.isdir, c.links, c.revision, # note: skip c.when
                  c.branch, c.category,
                  c.revlink, c.properties.asList(),
                  c.repository, c.project ],
                [ u'djmitche', [ u'changes.py' ], u'I hate this file',
                  0, [], None,
                  None, None,
                  '', [],
                  '', ''])

    def test_constructor_isdir(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                isdir=1)
        self.assertEqual(c.isdir, 1)

    def test_constructor_links(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                links=['http://buildbot.net'])
        self.assertEqual(c.links, ['http://buildbot.net'])

    def test_constructor_revision_int(self):
        self.assertRaises(ValueError,
            lambda : changes.Change(u'me', [ u'foo.c' ], u'fixes',
                revision=456))

    def test_constructor_revision_str(self):
        self.assertRaises(ValueError,
            lambda : changes.Change(u'me', [ u'foo.c' ], u'fixes',
                revision='456'))

    def test_constructor_revision_unicode(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                revision=u'456')
        self.assertEqualUnicode(c.revision, u'456')

    def test_constructor_when(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                when=1273727073)
        self.assertEqual(c.when, 1273727073)

    def test_constructor_branch_str(self):
        self.assertRaises(ValueError,
            lambda : changes.Change(u'me', [ u'foo.c' ], u'fixes',
                branch='branches/release'))

    def test_constructor_branch_unicode(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                branch=u'branches/release')
        self.assertEqualUnicode(c.branch, u'branches/release')

    def test_constructor_category_str(self):
        self.assertRaises(ValueError,
            lambda : changes.Change(u'me', [ u'foo.c' ], u'fixes',
                category='important'))

    def test_constructor_category_unicode(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                category=u'important')
        self.assertEqualUnicode(c.category, u'important')

    def test_constructor_revlink_str(self):
        self.assertRaises(ValueError,
            lambda : changes.Change(u'me', [ u'foo.c' ], u'fixes',
                revlink='http://buildbot.net'))

    def test_constructor_revlink_unicode(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                revlink=u'http://buildbot.net')
        self.assertEqualUnicode(c.revlink, u'http://buildbot.net')

    def test_constructor_repository_str(self):
        self.assertRaises(ValueError,
            lambda : changes.Change(u'me', [ u'foo.c' ], u'fixes',
                repository='http://svn.buildbot.net'))

    def test_constructor_repository_unicode(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                repository=u'http://svn.buildbot.net')
        self.assertEqualUnicode(c.repository, u'http://svn.buildbot.net')

    def test_constructor_project_str(self):
        self.assertRaises(ValueError,
            lambda : changes.Change(u'me', [ u'foo.c' ], u'fixes',
                project='buildbot'))

    def test_constructor_project_unicode(self):
        c = changes.Change(u'me', [ u'foo.c' ], u'fixes',
                project=u'buildbot')
        self.assertEqualUnicode(c.project, u'buildbot')

    def test_asDict(self):
        c = self.getBigChange()
        self.assertEqual(c.asDict(), dict(
            number=None,
            branch=u'branches/release',
            category=u'important',
            who=u'me',
            comments=u'fixes',
            revision=u'456',
            rev=u'456',
            when=1273727073,
            at=time.strftime("%a %d %b %Y %H:%M:%S", time.localtime(1273727073)),
            files=[dict(name=u'foo.c', url=None)],
            revlink='http://buildbot.net',
            properties=[('foo', 'bar', 'Change')],
            repository=u'http://svn.buildbot.net',
            project=u'buildbot'))

    def test_getTime_None(self):
        c = self.getBigChange()
        self.assertEqual(c.getTime(),
                time.strftime("%a %d %b %Y %H:%M:%S", time.localtime(1273727073)))

    def test_getTimes(self):
        c = self.getBigChange()
        self.assertEqual(c.getTimes(), (1273727073, None))

    def test_getText(self):
        c = self.getBigChange()
        self.assertEqual(c.getText(), [u'me'])

    def test_getText_htmlunsafe(self):
        c = changes.Change(u'>hi<', [ u'foo.c' ], u'fixes')
        self.assertEqual(c.getText(), [u'&gt;hi&lt;'])
