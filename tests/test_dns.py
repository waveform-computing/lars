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

import socket

import pytest
import mock

from lars import dns


def test_from_address():
    with mock.patch('tests.test_dns.dns.socket.getnameinfo') as getnameinfo:
        getnameinfo.return_value = ('9.0.0.0', 0)
        dns.from_address('9.0.0.0')
        assert getnameinfo.called_with(('9.0.0.0', 0), 0)
        getnameinfo.return_value = ('0.0.0.0', 0)
        dns.from_address('0.0.0.0')
        assert getnameinfo.called_with(('0.0.0.0', 0), 0)

def test_to_address():
    with mock.patch('tests.test_dns.dns.socket.getaddrinfo') as getaddrinfo:
        getaddrinfo.return_value = [(socket.AF_INET, 0, 0, 0, ('127.0.0.1', 0))]
        assert dns.to_address('localhost') == '127.0.0.1'
        getaddrinfo.return_value = [(socket.AF_INET6, 0, 0, 0, ('::1', 0, 0, 0))]
        assert dns.to_address('ip6-localhost') == '::1'
        # Ensure IPv4 is always preferred over IPv6, if available
        getaddrinfo.return_value = [
            (socket.AF_INET6, 0, 0, 0, ('::1', 0, 0, 0)),
            (socket.AF_INET6, 0, 0, 0, ('::2', 0, 0, 0)),
            (socket.AF_INET, 0, 0, 0, ('127.0.0.1', 0)),
            ]
        assert dns.to_address('dualstack-localhost') == '127.0.0.1'

