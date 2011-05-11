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

import string
import random
from twisted.trial import unittest
from twisted.internet import defer
from buildbot.util import lru

class LRUCache(unittest.TestCase):

    def setUp(self):
        self.lru = lru.AsyncLRUCache(3)

    def regular_miss_fn(self, key):
        return defer.succeed(key.upper() * 3)

    def longer_miss_fn(self, key):
        return defer.succeed(key.upper() * 6)

    def failure_miss_fn(self, key):
        return defer.succeed(None)

    def check_result(self, r, exp, exp_hits=None, exp_misses=None):
        self.assertEqual(r, exp)
        if exp_hits is not None:
            self.assertEqual(self.lru.hits, exp_hits)
        if exp_misses is not None:
            self.assertEqual(self.lru.misses, exp_misses)

    # tests

    def test_single_key(self):
        # just get an item
        d = self.lru.get('a', self.regular_miss_fn)
        d.addCallback(self.check_result, 'AAA', 0, 1)

        # second time, it should be cached..
        d.addCallback(lambda _ :
            self.lru.get('a', self.longer_miss_fn))
        d.addCallback(self.check_result, 'AAA', 1, 1)
        return d

    def test_simple_lru_expulsion(self):
        d = defer.succeed(None)

        d.addCallback(lambda _ :
            self.lru.get('a', self.regular_miss_fn))
        d.addCallback(self.check_result, 'AAA', 0, 1)
        d.addCallback(lambda _ :
            self.lru.get('b', self.regular_miss_fn))
        d.addCallback(self.check_result, 'BBB', 0, 2)
        d.addCallback(lambda _ :
            self.lru.get('c', self.regular_miss_fn))
        d.addCallback(self.check_result, 'CCC', 0, 3)
        d.addCallback(lambda _ :
            self.lru.get('d', self.regular_miss_fn))
        d.addCallback(self.check_result, 'DDD', 0, 4)

        # now try 'a' again - it should be a miss
        d.addCallback(lambda _ :
            self.lru.get('a', self.longer_miss_fn))
        d.addCallback(self.check_result, 'AAAAAA', 0, 5)

        # ..and that expelled B, but C is still in the cache
        d.addCallback(lambda _ :
            self.lru.get('c', self.longer_miss_fn))
        d.addCallback(self.check_result, 'CCC', 1, 5)
        return d

    @defer.deferredGenerator
    def test_queue_collapsing(self):
        # just to check that we're practicing with the right queue size
        self.assertEqual(self.lru.max_queue, 30)

        for c in 'a' + 'x' * 27 + 'ab':
            wfd = defer.waitForDeferred(
                    self.lru.get(c, self.regular_miss_fn))
            yield wfd
            res = wfd.getResult()
        self.check_result(res, 'BBB', 27, 3)

        # at this point, we should have 'x', 'a', and 'b' in the cache,
        # and a, lots of x's, and ab in the queue.  The next get operation
        # should evict 'x', not 'a'.

        wfd = defer.waitForDeferred(
                self.lru.get('c', self.regular_miss_fn))
        yield wfd
        res = wfd.getResult()
        self.check_result(res, 'CCC', 27, 4)

        # expect a cached 'AAA'
        wfd = defer.waitForDeferred(
                self.lru.get('a', self.longer_miss_fn))
        yield wfd
        res = wfd.getResult()
        self.check_result(res, 'AAA', 28, 4)

        # expect a newly minted 'XXXXXX'
        wfd = defer.waitForDeferred(
                self.lru.get('x', self.longer_miss_fn))
        yield wfd
        res = wfd.getResult()
        self.check_result(res, 'XXXXXX', 28, 5)

    @defer.deferredGenerator
    def test_all_misses(self):
        for i, c in enumerate(string.lowercase + string.uppercase):
            wfd = defer.waitForDeferred(
                    self.lru.get(c, self.regular_miss_fn))
            yield wfd
            res = wfd.getResult()
            self.check_result(res, c.upper() * 3, 0, i+1)

    @defer.deferredGenerator
    def test_all_hits(self):
        wfd = defer.waitForDeferred(
                self.lru.get('a', self.regular_miss_fn))
        yield wfd
        res = wfd.getResult()
        self.check_result(res, 'AAA', 0, 1)

        for i in xrange(100):
            wfd = defer.waitForDeferred(
                    self.lru.get('a', self.longer_miss_fn))
            yield wfd
            res = wfd.getResult()
            self.check_result(res, 'AAA', i+1, 1)

    @defer.deferredGenerator
    def test_fuzz(self):
        chars = list(string.lowercase * 40)
        random.shuffle(chars)
        for i, c in enumerate(chars):
            wfd = defer.waitForDeferred(
                    self.lru.get(c, self.regular_miss_fn))
            yield wfd
            res = wfd.getResult()
            self.check_result(res, c.upper() * 3)
