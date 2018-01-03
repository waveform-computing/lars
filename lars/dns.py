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

"""
This module provides a couple of trivial DNS resolution functions, enhanced
with LRU caches. Most users should never need to access these functions
directly.  Instead, use the :attr:`~lars.datatypes.Hostname.address` and
:attr:`~lars.datatypes.IPv4Address.hostname` properties of relevant objects.


Functions
=========

"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import socket

from lars.cache import lru_cache

str = type('')  # pylint: disable=redefined-builtin,invalid-name


@lru_cache(maxsize=10000)
def from_address(address):
    """
    Reverse resolve an address to a hostname.

    Given a string containing an IPv4 or IPv6 address, this functions returns
    a hostname associated with the address, using an LRU cache to speed up
    repeat queries. If the address does not reverse, the function returns
    the original address.

    :param str address: The address to resolve to a hostname
    :returns: The resolved hostname
    """
    if ':' in address:
        # XXX Need to consider what (if anything) we should be doing with the
        # scope-id field here
        sockaddr = (address, 0, 0, 0)
    else:
        sockaddr = (address, 0)
    return socket.getnameinfo(sockaddr, 0)[0]


@lru_cache(maxsize=10000)
def to_address(hostname, family=socket.AF_UNSPEC, socktype=socket.SOCK_STREAM):
    """
    Resolve a hostname to an address, preferring IPv4 addresses.

    Given a string containing a DNS hostname, this function resolves the
    hostname to an address, using an LRU cache to speed up repeat queries. The
    function prefers IPv4 addresses, but will return IPv6 addresses if no IPv4
    addresses are present in the result from getaddrinfo. If the hostname does
    not resolve, the function returns None rather than raise an exception (this
    is preferable as it provides a negative lookup cache).

    :param str hostname: The hostname to resolve to an address
    :returns: The resolved address
    """
    result = None
    try:
        for (family, _, _, _, sockaddr) in socket.getaddrinfo(
                hostname, None, family, socktype):
            if family == socket.AF_INET:
                result = sockaddr[0]
                break
            elif family == socket.AF_INET6 and not result:
                result = sockaddr[0]
    # XXX Workaround LP #1154599
    # This should be socket.gaierror instead of socket.error
    except socket.error:
        pass
    return result
