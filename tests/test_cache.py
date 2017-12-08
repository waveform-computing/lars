# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright (c) 2013-2017 Dave Jones <dave@waveform.org.uk>
# Copyright (c) 2013 Mime Consulting Ltd. <info@mimeconsulting.co.uk>
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import pytest

from lars import cache


@cache.lru_cache(maxsize=5)
def double_lru(x):
    return 2 * x


def test_lru_cache():
    # Some simple calls to populate the cache
    assert double_lru(1) == 2
    assert double_lru(2) == 4
    assert double_lru(3) == 6
    assert double_lru(4) == 8
    assert double_lru(5) == 10
    assert double_lru.cache_info()[:2] == (0, 5)
    # Try four calls which should hit the cache
    assert double_lru(2) == 4
    assert double_lru(3) == 6
    assert double_lru(4) == 8
    assert double_lru(5) == 10
    # Try another call which should force "1" out of the cache
    assert double_lru(6) == 12
    assert double_lru.cache_info()[:2] == (4, 6)
    # Ensure calling with "1" causes another miss
    assert double_lru(1) == 2
    assert double_lru.cache_info()[:2] == (4, 7)
    # Make several more cached calls to force a queue compaction and test
    # the cache keeps working and returning the right results
    last_hits = double_lru.cache_info()[0]
    for n in range(50):
        assert double_lru.cache_info()[0] == last_hits + n
        assert double_lru(1) == 2
    double_lru.cache_clear()
    assert double_lru.cache_info()[:2] == (0, 0)
    assert double_lru(1) == 2
    assert double_lru.cache_info()[:2] == (0, 1)
    # Check that calling with a float instead of an int is still cached
    assert double_lru(1.0) == 2
    assert double_lru.cache_info()[:2] == (1, 1)
    # Try some other hashable types with the call
    assert double_lru((1, 2)) == (1, 2, 1, 2)
    assert double_lru.cache_info()[:2] == (1, 2)
    assert double_lru('aa') == 'aaaa'
    assert double_lru.cache_info()[:2] == (1, 3)

