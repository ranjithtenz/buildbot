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

from itertools import ifilterfalse
from twisted.internet import defer
from collections import deque
from buildbot.util.bbcollections import defaultdict

class AsyncLRUCache(object):
    """

    A least-recently-used cache, with a fixed maximum size.

    This cache is designed to memoize asynchronous functions, and uses minimal
    locking to ensure that a value is only calculated once at any given time.

    This is based on Raymond Hettinger's implementation in
    U{http://code.activestate.com/recipes/498245-lru-and-lfu-cache-decorators/}
    licensed under the PSF license, which is GPL-compatiblie.

    @ivar hits: cache hits so far
    @ivar misses: cache misses so far
    """

    # TODO: per-item locking (list of deferreds to call with result or errback)
    # TODO: backup WeakValueDictionary

    __slots__ = 'max_size max_queue queue cache refcount hits misses'.split()
    sentinel = object()

    def __init__(self, max_size=50):
        self.max_size = max_size
        self.max_queue = max_size * 10
        self.queue = deque()
        self.cache = {}
        self.hits = self.misses = 0
        self.refcount = defaultdict(default_factory = lambda : 0)

    @defer.deferredGenerator
    def get(self, key, miss_fn):
        """
        Fetch a value from the cache by key, invoking C{miss_fn(key)} if the
        key is not in the cache.  The C{miss_fn} should return a Deferred.

        @param key: cache key
        @param miss_fn: function to call for cache misses
        @returns: value via Deferred
        """
        cache = self.cache
        refcount = self.refcount
        queue = self.queue

        # record recent use of this key
        queue.append(key)
        refcount[key] = refcount.get(key, 0) + 1

        try:
            result = cache[key]
            self.hits += 1
        except KeyError:
            wfd = defer.waitForDeferred(
                    miss_fn(key))
            yield wfd
            result = wfd.getResult()

            cache[key] = result
            self.misses += 1

            # purge least recently used entry, using refcount
            # to count repeatedly-used entries
            if len(cache) > self.max_size:
                refc = 1
                while refc:
                    key = queue.popleft()
                    refc = refcount[key] = refcount[key] - 1
                del cache[key], refcount[key]

        # periodically compact the queue by eliminating duplicate keys
        # while preserving order of most recent access
        if len(queue) > self.max_queue:
            refcount.clear()
            queue_appendleft = queue.appendleft
            queue_appendleft(self.sentinel)
            for key in ifilterfalse(refcount.__contains__,
                                    iter(queue.pop, self.sentinel)):
                queue_appendleft(key)
                refcount[key] = 1

        # return the result
        yield result
