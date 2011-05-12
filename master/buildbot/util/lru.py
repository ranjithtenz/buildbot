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

from weakref import WeakValueDictionary
from itertools import ifilterfalse
from twisted.internet import defer
from collections import deque
from buildbot.util.bbcollections import defaultdict

class AsyncLRUCache(object):
    """

    A least-recently-used cache, with a fixed maximum size.  This cache is
    designed to control memory usage by minimizing duplication of objects,
    while avoiding unnecessary re-fetching of the same rows from the database.

    Asynchronous locking is used to ensure that in the common case of multiple
    concurrent requests for the same key, only one fetch is performed.
    (TODO)

    All values are also stored in a weak valued dictionary, even after they
    have expired from the cache.  This allows values that are used elsewhere in
    Buildbot to "stick" in the cache in case they are needed by another
    component.  Weak references cannot be used for some types, so these types
    are not compatible with this class.  Note that dictionaries can be weakly
    referenced if they are an instance of a subclass of C{dict}.

    This is based on Raymond Hettinger's implementation in
    U{http://code.activestate.com/recipes/498245-lru-and-lfu-cache-decorators/}
    licensed under the PSF license, which is GPL-compatiblie.

    @ivar hits: cache hits so far
    @ivar refhits: cache misses found in the weak ref dictionary, so far
    @ivar misses: cache misses leading to re-fetches, so far
    """

    __slots__ = ('max_size max_queue queue cache weakrefs refcount ' 
                 'hits refhits misses'.split())
    sentinel = object()

    def __init__(self, max_size=50):
        self.max_size = max_size
        self.max_queue = max_size * 10
        self.queue = deque()
        self.cache = {}
        self.weakrefs = WeakValueDictionary()
        self.hits = self.misses = self.refhits = 0
        self.refcount = defaultdict(default_factory = lambda : 0)

    def get(self, key, miss_fn):
        """
        Fetch a value from the cache by key, invoking C{miss_fn(key)} if the
        key is not in the cache.  The C{miss_fn} should return a Deferred.

        @param key: cache key
        @param miss_fn: function to call for cache misses
        @returns: value via Deferred
        """
        cache = self.cache
        weakrefs = self.weakrefs
        refcount = self.refcount
        queue = self.queue

        # record recent use of this key
        queue.append(key)
        refcount[key] = refcount.get(key, 0) + 1

        try:
            result = cache[key]
            self.hits += 1
            return defer.succeed(result)
        except KeyError:
            try:
                result = weakrefs[key]
                self.refhits += 1
                cache[key] = result
                return defer.succeed(result)
            except KeyError:
                pass

        # if we're here, we've missed and need to fetch
        self.misses += 1

        # chain in the miss_fn invocation and keep the result
        d = miss_fn(key)

        def cleanup(result):
            cache[key] = result
            weakrefs[key] = result

            # purge least recently used entry, using refcount
            # to count repeatedly-used entries
            if len(cache) > self.max_size:
                refc = 1
                while refc:
                    k = queue.popleft()
                    refc = refcount[k] = refcount[k] - 1
                del cache[k], refcount[k]

            # periodically compact the queue by eliminating duplicate keys
            # while preserving order of most recent access
            if len(queue) > self.max_queue:
                refcount.clear()
                queue_appendleft = queue.appendleft
                queue_appendleft(self.sentinel)
                for k in ifilterfalse(refcount.__contains__,
                                        iter(queue.pop, self.sentinel)):
                    queue_appendleft(k)
                    refcount[k] = 1

            return result
        d.addCallback(cleanup)

        return d
