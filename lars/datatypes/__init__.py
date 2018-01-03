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
This module wraps various Python data-types which are commonly found in log
files to provide them with default string coercions and enhanced attributes.
Each datatype is given a simple constructor function which accepts a string in
a common format (for example, the :func:`date` function which accepts dates in
``YYYY-MM-DD`` format), and returns the converted data.

Most of the time you will not need the functions in this module directly, but
the attributes of the classes are extremely useful for filtering and
transforming log data for output.


Classes
=======

.. autoclass:: DateTime
   :members:

.. autoclass:: Date
   :members:

.. autoclass:: Hostname
   :members: address

.. autoclass:: IPv4Address
   :members:

.. autoclass:: IPv4Network
   :members:

.. autoclass:: IPv4Port
   :members:

.. autoclass:: IPv6Address
   :members:

.. autoclass:: IPv6Network
   :members:

.. autoclass:: IPv6Port
   :members:

.. autoclass:: Path
   :members:

.. autoclass:: Time
   :members:

.. autoclass:: Url
   :members:


Functions
=========

.. autofunction:: address

.. autofunction:: date

.. autofunction:: datetime

.. autofunction:: hostname

.. autofunction:: network

.. autofunction:: path

.. autofunction:: row

.. autofunction:: time

.. autofunction:: url


.. _RFC 1918: http://tools.ietf.org/html/rfc1918
.. _RFC 2373 2.5.2: http://tools.ietf.org/html/rfc2373#section-2.5.2
.. _RFC 2373 2.5.3: http://tools.ietf.org/html/rfc2373#section-2.5.3
.. _RFC 2373 2.7: http://tools.ietf.org/html/rfc2373#section-2.7
.. _RFC 3171: http://tools.ietf.org/html/rfc3171
.. _RFC 3330: http://tools.ietf.org/html/rfc3330
.. _RFC 3513 2.5.6: http://tools.ietf.org/html/rfc3513#section-2.5.6
.. _RFC 3879: http://tools.ietf.org/html/rfc3879
.. _RFC 3927: http://tools.ietf.org/html/rfc3927
.. _RFC 4291: http://tools.ietf.org/html/rfc4291
.. _RFC 4193: http://tools.ietf.org/html/rfc4193
.. _RFC 5735 3: http://tools.ietf.org/html/rfc5735#section-3
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import re
import datetime as dt
import sqlite3
from collections import namedtuple

# This module collects various sub-modules together; don't warn about unused
# imports (F401)
from .datetime import date, time, datetime, Date, Time, DateTime  # noqa: F401
from .ipaddress import (  # noqa: F401
    hostname, address, network,
    Hostname,
    IPv4Address, IPv6Address,
    IPv4Network, IPv6Network,
    IPv4Port, IPv6Port)
from .url import path, url, request, Path, Url, Request  # noqa: F401

native_str = str  # pylint: disable=invalid-name
str = type('')  # pylint: disable=redefined-builtin,invalid-name


def sanitize_name(name):
    """
    Sanitizes the given name for use as a Python identifier.

    :param str name: The name to sanitize
    :returns str: The sanitized name, suitable for use as an identifier
    """
    if name == '':
        raise ValueError('Cannot sanitize a blank string')
    return (
        re.sub(r'[^A-Za-z_]', '_', name[:1]) +
        re.sub(r'[^A-Za-z0-9_]+', '_', name[1:])
    )


def row(*args):
    """
    Returns a new tuple sub-class type containing the specified fields. For
    example::

        NewRow = row('foo', 'bar', 'baz')
        a_row = NewRow(1, 2, 3)
        print(a_row.foo)

    :param \\*args: The set of fields to include in the row definition.
    :returns: A tuple sub-class with the specified fields.
    """
    return namedtuple('Row', args)


# Here we register our derivative Date, Time and DateTime classes with
# sqlite3's adapter registry. This is necessary as the register doesn't handle
# derivative types. While we're at it, we register adapters and convertors for
# the datetime.time type as well which is bizarrely missing from the
# original...

def register_adapters_and_converters():
    # pylint: disable=invalid-name,missing-docstring

    def adapt_date(val):
        return val.isoformat()

    def adapt_time(val):
        return val.isoformat()

    def adapt_datetime(val):
        return val.isoformat(native_str(" "))

    def convert_date(val):
        return Date(*(int(v) for v in val.split(b"-")))

    def convert_time(val):
        return Time(*(int(v) for v in val.split(b":")))

    def convert_timestamp(val):
        datepart, timepart = val.split(b" ")
        year, month, day = (int(v) for v in datepart.split(b"-"))
        timepart_full = timepart.split(b".")
        hours, minutes, seconds = (
            int(v) for v in timepart_full[0].split(b":"))
        if len(timepart_full) == 2:
            microseconds = int(timepart_full[1])
        else:
            microseconds = 0
        val = DateTime(year, month, day, hours, minutes, seconds, microseconds)
        return val

    sqlite3.register_adapter(dt.date, adapt_date)
    sqlite3.register_adapter(Date, adapt_date)
    sqlite3.register_adapter(dt.time, adapt_time)
    sqlite3.register_adapter(Time, adapt_time)
    sqlite3.register_adapter(dt.datetime, adapt_datetime)
    sqlite3.register_adapter(DateTime, adapt_datetime)
    sqlite3.register_converter(native_str("date"), convert_date)
    sqlite3.register_converter(native_str("time"), convert_time)
    sqlite3.register_converter(native_str("timestamp"), convert_timestamp)

register_adapters_and_converters()
# Clean up namespace
del register_adapters_and_converters
