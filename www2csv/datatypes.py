# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright (c) 2013 Dave Hughes
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
#
#
# The documentation for the DateTime, Date, and Time classes in this module are
# derived from the documentation sources for the datetime, date, and time
# classes in Python 2.7.4 and thus are subject to the following copyright and
# license:
#
# Copyright (c) 1990-2013, Python Software Foundation
#
# PSF LICENSE AGREEMENT FOR PYTHON 2.7.4
#
# 1. This LICENSE AGREEMENT is between the Python Software Foundation
#    (“PSF”), and the Individual or Organization (“Licensee”) accessing
#    and otherwise using Python 2.7.4 software in source or binary form and its
#    associated documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF hereby
#    grants Licensee a nonexclusive, royalty-free, world-wide license to
#    reproduce, analyze, test, perform and/or display publicly, prepare
#    derivative works, distribute, and otherwise use Python 2.7.4 alone or in
#    any derivative version, provided, however, that PSF’s License Agreement
#    and PSF’s notice of copyright, i.e., “Copyright © 2001-2013 Python
#    Software Foundation; All Rights Reserved” are retained in Python 2.7.4
#    alone or in any derivative version prepared by Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on or
#    incorporates Python 2.7.4 or any part thereof, and wants to make the
#    derivative work available to others as provided herein, then Licensee
#    hereby agrees to include in any such work a brief summary of the changes
#    made to Python 2.7.4.
#
# 4. PSF is making Python 2.7.4 available to Licensee on an “AS IS” basis.
#    PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED. BY WAY OF
#    EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION
#    OR WARRANTY OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR
#    THAT THE USE OF PYTHON 2.7.4 WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON 2.7.4
#    FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT
#    OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 2.7.4, OR ANY
#    DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material breach
#    of its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any
#    relationship of agency, partnership, or joint venture between PSF and
#    Licensee. This License Agreement does not grant permission to use PSF
#    trademarks or trade name in a trademark sense to endorse or promote
#    products or services of Licensee, or any third party.
#
# 8. By copying, installing or otherwise using Python 2.7.4, Licensee agrees to
#    be bound by the terms and conditions of this License Agreement.
#
#
# The documentation for the IPv4Address, IPv4Network, IPv6Address, and IPv6Network
# classes in this module are derived from the ipaddress documentation sources
# which are subject to the following copyright and are licensed to the PSF
# under the contributor agreement which makes them subject to the PSF license
# stated above.
#
# Copyright (c) 2007 Google Inc.

"""
This module wraps various Python data-types which are commonly found in log
files to provide them with default string coercions and enhanced attributes.
Each datatype is given a simple constructor which accepts a string in a common
format (for example, the :func:`date` function which accepts dates in
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

import sys
import os
import re
import datetime as dt
import urlparse
import ipaddress
from collections import namedtuple
from functools import total_ordering

from www2csv import geoip, dns


# XXX Make Py2 str same as Py3
str = type('')


def datetime(s, format='%Y-%m-%d %H:%M:%S'):
    """
    Returns a :class:`DateTime` object for the given string.

    :param str s: The string containing the timestamp to parse
    :param str format: Optional string containing the datetime format to parse
    :returns: A :class:`DateTime` object representing the timestamp
    """
    return DateTime.strptime(s, format)


def date(s, format='%Y-%m-%d'):
    """
    Returns a :class:`Date` object for the given string.

    :param str s: The string containing the date to parse
    :param str format: Optional string containing the date format to parse
    :returns: A :class:`Date` object representing the date
    """
    return DateTime.strptime(s, format).date()


def time(s, format='%H:%M:%S'):
    """
    Returns a :class:`Time` object for the given string.

    :param str s: The string containing the time to parse
    :param str format: Optional string containing the time format to parse
    :returns: A :class:`Time` object representing the time
    """
    return DateTime.strptime(s, format).time()


def path(s):
    """
    Returns a :class:`Path` object for the given string.

    :param str s: The string containing the path to parse
    :returns: A :class:`Path` object representing the path
    """
    return Path(s)


def url(s):
    """
    Returns a :class:`Url` object for the given string.

    :param str s: The string containing the URL to parse
    :returns: A :class:`Url` tuple representing the URL
    """
    return Url(*urlparse.urlparse(s))


def hostname(s):
    """
    Returns a :class:`Hostname` object for the given string.

    :param str s: The string containing the hostname to parse
    :returns: A :class:`Hostname` instance
    """
    return Hostname(s)


def network(s):
    """
    Returns an :class:`IPv4Network` or :class:`IPv6Network` instance for the
    given string.

    :param str s: The string containing the IP network to parse
    :returns: An :class:`IPv4Network` or :class:`IPv6Network` instance
    """
    if isinstance(s, bytes):
        s = str(s)
    try:
        return IPv4Network(s)
    except ValueError:
        pass
    try:
        return IPv6Network(s)
    except ValueError:
        pass
    raise ValueError(
        '%s does not appear to be a valid IPv4 or IPv6 network' % s)


def address(s):
    """
    Returns an :class:`IPv4Address`, :class:`IPv6Address`, :class:`IPv4Port`,
    or :class:`IPv6Port` instance for the given string.

    :param str s: The string containing the IP address to parse
    :returns: An :class:`IPv4Address`, :class:`IPv4Port`, :class:`IPv6Address`,
              or :class:`IPv6Port` instance
    """
    if isinstance(s, bytes):
        s = str(s)
    try:
        return IPv4Address(s)
    except ValueError:
        pass
    try:
        return IPv6Address(s)
    except ValueError:
        pass
    try:
        return IPv4Port(s)
    except ValueError:
        pass
    try:
        return IPv6Port(s)
    except ValueError:
        pass
    raise ValueError(
        '%s does not appear to be a valid IPv4 or IPv6 address' % s)


class DateTime(dt.datetime):
    """
    Represents a timestamp.

    This type is returned by the :func:`datetime` function and represents a
    timestamp (with optional timezone). A :class:`DateTime` object is a single
    object containing all the information from a :class:`Date` object and a
    :class:`Time` object.  Like a :class:`Date` object, :class:`DateTime`
    assumes the current Gregorian calendar extended in both directions; like a
    time object, :class:`DateTime` assumes there are exactly 3600\*24 seconds
    in every day.

    Other constructors, all class methods:

    .. classmethod:: today()

       Return the current local datetime, with :attr:`tzinfo` ``None``. This is
       equivalent to ``DateTime.fromtimestamp(time.time())``. See also
       :meth:`now`, :meth:`fromtimestamp`.

    .. classmethod:: now([tz])

       Return the current local date and time.  If optional argument *tz* is
       ``None`` or not specified, this is like :meth:`today`, but, if possible,
       supplies more precision than can be gotten from going through a
       :func:`time.time` timestamp (for example, this may be possible on
       platforms supplying the C :c:func:`gettimeofday` function).

       Else *tz* must be an instance of a class :class:`tzinfo` subclass, and
       the current date and time are converted to *tz*'s time zone.  In this
       case the result is equivalent to
       ``tz.fromutc(DateTime.utcnow().replace(tzinfo=tz))``.  See also
       :meth:`today`, :meth:`utcnow`.

    .. classmethod:: utcnow()

       Return the current UTC date and time, with :attr:`tzinfo` ``None``. This
       is like :meth:`now`, but returns the current UTC date and time, as a
       naive :class:`DateTime` object. See also :meth:`now`.

    .. classmethod:: fromtimestamp(timestamp[, tz])

       Return the local date and time corresponding to the POSIX timestamp,
       such as is returned by :func:`time.time`. If optional argument *tz* is
       ``None`` or not specified, the timestamp is converted to the platform's
       local date and time, and the returned :class:`DateTime` object is naive.

       Else *tz* must be an instance of a class :class:`tzinfo` subclass, and
       the timestamp is converted to *tz*'s time zone.  In this case the result
       is equivalent to
       ``tz.fromutc(DateTime.utcfromtimestamp(timestamp).replace(tzinfo=tz))``.

       :meth:`fromtimestamp` may raise :exc:`ValueError`, if the timestamp is
       out of the range of values supported by the platform C
       :c:func:`localtime` or :c:func:`gmtime` functions.  It's common for this
       to be restricted to years in 1970 through 2038. Note that on non-POSIX
       systems that include leap seconds in their notion of a timestamp, leap
       seconds are ignored by :meth:`fromtimestamp`, and then it's possible to
       have two timestamps differing by a second that yield identical
       :class:`DateTime` objects. See also :meth:`utcfromtimestamp`.

    .. classmethod:: utcfromtimestamp(timestamp)

       Return the UTC :class:`DateTime` corresponding to the POSIX timestamp,
       with :attr:`tzinfo` ``None``. This may raise :exc:`ValueError`, if the
       timestamp is out of the range of values supported by the platform C
       :c:func:`gmtime` function.  It's common for this to be restricted to
       years in 1970 through 2038. See also :meth:`fromtimestamp`.

    .. classmethod:: combine(date, time)

       Return a new :class:`DateTime` object whose date components are equal to
       the given :class:`date` object's, and whose time components and
       :attr:`tzinfo` attributes are equal to the given :class:`Time`
       object's. For any :class:`DateTime` object *d*, ``d ==
       DateTime.combine(d.date(), d.timetz())``.  If date is a
       :class:`DateTime` object, its time components and :attr:`tzinfo`
       attributes are ignored.

    .. classmethod:: strptime(date_string, format)

       Return a :class:`DateTime` corresponding to *date_string*, parsed
       according to *format*.  This is equivalent to
       ``DateTime(*(time.strptime(date_string, format)[0:6]))``.
       :exc:`ValueError` is raised if the date_string and format can't be
       parsed by :func:`time.strptime` or if it returns a value which isn't a
       time tuple.

    Class attributes:

    .. attribute:: min

       The earliest representable :class:`DateTime`.

    .. attribute:: max

       The latest representable :class:`DateTime`.

    .. attribute:: resolution

       The smallest possible difference between non-equal :class:`DateTime`
       objects, ``timedelta(microseconds=1)``.


    Instance attributes (read-only):

    .. attribute:: year

       Between :const:`MINYEAR` and :const:`MAXYEAR` inclusive.

    .. attribute:: month

       Between 1 and 12 inclusive.

    .. attribute:: day

       Between 1 and the number of days in the given month of the given year.

    .. attribute:: hour

       In ``range(24)``.

    .. attribute:: minute

       In ``range(60)``.

    .. attribute:: second

       In ``range(60)``.

    .. attribute:: microsecond

       In ``range(1000000)``.

    .. attribute:: tzinfo

       The object passed as the *tzinfo* argument to the :class:`DateTime`
       constructor, or ``None`` if none was passed.


    Supported operations:

    +---------------------------------------+--------------------------------+
    | Operation                             | Result                         |
    +=======================================+================================+
    | ``datetime2 = datetime1 + timedelta`` | \(1)                           |
    +---------------------------------------+--------------------------------+
    | ``datetime2 = datetime1 - timedelta`` | \(2)                           |
    +---------------------------------------+--------------------------------+
    | ``timedelta = datetime1 - datetime2`` | \(3)                           |
    +---------------------------------------+--------------------------------+
    | ``datetime1 < datetime2``             | Compares :class:`DateTime` to  |
    |                                       | :class:`DateTime`. (4)         |
    +---------------------------------------+--------------------------------+

    #. datetime2 is a duration of timedelta removed from datetime1, moving
       forward in time if ``timedelta.days`` > 0, or backward if
       ``timedelta.days`` < 0.  The result has the same :attr:`tzinfo`
       attribute as the input datetime, and datetime2 - datetime1 == timedelta
       after. :exc:`OverflowError` is raised if datetime2.year would be smaller
       than :const:`MINYEAR` or larger than :const:`MAXYEAR`. Note that no time
       zone adjustments are done even if the input is an aware object.

    #. Computes the datetime2 such that datetime2 + timedelta == datetime1. As
       for addition, the result has the same :attr:`tzinfo` attribute as the
       input datetime, and no time zone adjustments are done even if the input
       is aware.  This isn't quite equivalent to datetime1 + (-timedelta),
       because -timedelta in isolation can overflow in cases where datetime1 -
       timedelta does not.

    #. Subtraction of a :class:`DateTime` from a :class:`DateTime` is defined
       only if both operands are naive, or if both are aware.  If one is aware
       and the other is naive, :exc:`TypeError` is raised.

       If both are naive, or both are aware and have the same :attr:`tzinfo`
       attribute, the :attr:`tzinfo` attributes are ignored, and the result is
       a :class:`timedelta` object *t* such that ``datetime2 + t ==
       datetime1``.  No time zone adjustments are done in this case.

       If both are aware and have different :attr:`tzinfo` attributes, ``a-b``
       acts as if *a* and *b* were first converted to naive UTC datetimes
       first.  The result is ``(a.replace(tzinfo=None) - a.utcoffset()) -
       (b.replace(tzinfo=None)
       - b.utcoffset())`` except that the implementation never overflows.

    #. *datetime1* is considered less than *datetime2* when *datetime1*
       precedes *datetime2* in time.

       If one comparand is naive and the other is aware, :exc:`TypeError` is
       raised.  If both comparands are aware, and have the same :attr:`tzinfo`
       attribute, the common :attr:`tzinfo` attribute is ignored and the base
       datetimes are compared.  If both comparands are aware and have different
       :attr:`tzinfo` attributes, the comparands are first adjusted by
       subtracting their UTC offsets (obtained from ``self.utcoffset()``).

       .. note::

          In order to stop comparison from falling back to the default scheme
          of comparing object addresses, datetime comparison normally raises
          :exc:`TypeError` if the other comparand isn't also a
          :class:`DateTime` object.  However, ``NotImplemented`` is returned
          instead if the other comparand has a :meth:`timetuple` attribute.
          This hook gives other kinds of date objects a chance at implementing
          mixed-type comparison.  If not, when a :class:`DateTime` object is
          compared to an object of a different type, :exc:`TypeError` is raised
          unless the comparison is ``==`` or ``!=``.  The latter cases return
          :const:`False` or :const:`True`, respectively.

    :class:`DateTime` objects can be used as dictionary keys. In Boolean
    contexts, all :class:`DateTime` objects are considered to be true.

    Instance methods:

    .. method:: date()

       Return :class:`date` object with same year, month and day.

    .. method:: time()

       Return :class:`Time` object with same hour, minute, second and
       microsecond.  :attr:`tzinfo` is ``None``.  See also method
       :meth:`timetz`.

    .. method:: timetz()

       Return :class:`Time` object with same hour, minute, second,
       microsecond, and tzinfo attributes.  See also method :meth:`time`.

    .. method:: replace([year[, month[, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]]]]])

       Return a DateTime with the same attributes, except for those attributes
       given new values by whichever keyword arguments are specified.  Note
       that ``tzinfo=None`` can be specified to create a naive DateTime from an
       aware DateTime with no conversion of date and time data.

    .. method:: astimezone(tz)

       Return a :class:`DateTime` object with new :attr:`tzinfo` attribute
       *tz*, adjusting the date and time data so the result is the same UTC
       time as *self*, but in *tz*'s local time.

       *tz* must be an instance of a :class:`tzinfo` subclass, and its
       :meth:`utcoffset` and :meth:`dst` methods must not return ``None``.
       *self* must be aware (``self.tzinfo`` must not be ``None``, and
       ``self.utcoffset()`` must not return ``None``).

       If ``self.tzinfo`` is *tz*, ``self.astimezone(tz)`` is equal to *self*:
       no adjustment of date or time data is performed. Else the result is
       local time in time zone *tz*, representing the same UTC time as *self*:
       after ``astz = dt.astimezone(tz)``, ``astz - astz.utcoffset()`` will
       usually have the same date and time data as ``dt - dt.utcoffset()``. The
       discussion of class :class:`tzinfo` explains the cases at Daylight
       Saving Time transition boundaries where this cannot be achieved (an
       issue only if *tz* models both standard and daylight time).

       If you merely want to attach a time zone object *tz* to a DateTime *dt*
       without adjustment of date and time data, use ``dt.replace(tzinfo=tz)``.
       If you merely want to remove the time zone object from an aware DateTime
       *dt* without conversion of date and time data, use
       ``dt.replace(tzinfo=None)``.

       Note that the default :meth:`tzinfo.fromutc` method can be overridden in
       a :class:`tzinfo` subclass to affect the result returned by
       :meth:`astimezone`.  Ignoring error cases, :meth:`astimezone` acts
       like::

          def astimezone(self, tz):
              if self.tzinfo is tz:
                  return self
              # Convert self to UTC, and attach the new time zone object.
              utc = (self - self.utcoffset()).replace(tzinfo=tz)
              # Convert from UTC to tz's local time.
              return tz.fromutc(utc)

    .. method:: utcoffset()

       If :attr:`tzinfo` is ``None``, returns ``None``, else returns
       ``self.tzinfo.utcoffset(self)``, and raises an exception if the latter
       doesn't return ``None``, or a :class:`timedelta` object representing a
       whole number of minutes with magnitude less than one day.

    .. method:: dst()

       If :attr:`tzinfo` is ``None``, returns ``None``, else returns
       ``self.tzinfo.dst(self)``, and raises an exception if the latter doesn't
       return ``None``, or a :class:`timedelta` object representing a whole
       number of minutes with magnitude less than one day.

    .. method:: tzname()

       If :attr:`tzinfo` is ``None``, returns ``None``, else returns
       ``self.tzinfo.tzname(self)``, raises an exception if the latter doesn't
       return ``None`` or a string object,

    .. method:: weekday()

       Return the day of the week as an integer, where Monday is 0 and Sunday
       is 6.  The same as ``self.date().weekday()``. See also
       :meth:`isoweekday`.

    .. method:: isoweekday()

       Return the day of the week as an integer, where Monday is 1 and Sunday
       is 7.  The same as ``self.date().isoweekday()``. See also
       :meth:`weekday`, :meth:`isocalendar`.

    .. method:: isocalendar()

       Return a 3-tuple, (ISO year, ISO week number, ISO weekday).  The same as
       ``self.date().isocalendar()``.

    .. method:: isoformat([sep])

       Return a string representing the date and time in ISO 8601 format,
       YYYY-MM-DDTHH:MM:SS.mmmmmm or, if :attr:`microsecond` is 0,
       YYYY-MM-DDTHH:MM:SS

       If :meth:`utcoffset` does not return ``None``, a 6-character string is
       appended, giving the UTC offset in (signed) hours and minutes:
       YYYY-MM-DDTHH:MM:SS.mmmmmm+HH:MM or, if :attr:`microsecond` is 0
       YYYY-MM-DDTHH:MM:SS+HH:MM

       The optional argument *sep* (default ``'T'``) is a one-character
       separator, placed between the date and time portions of the result.  For
       example,

          >>> from datetime import tzinfo, timedelta, datetime
          >>> class TZ(tzinfo):
          ...     def utcoffset(self, dt): return timedelta(minutes=-399)
          ...
          >>> datetime(2002, 12, 25, tzinfo=TZ()).isoformat(' ')
          '2002-12-25 00:00:00-06:39'
    """

class Date(dt.date):
    """
    Represents a date.

    This type is returned by the :func:`date` function and represents a date.
    A :class:`Date` object represents a date (year, month and day) in an
    idealized calendar, the current Gregorian calendar indefinitely extended in
    both directions.  January 1 of year 1 is called day number 1, January 2 of
    year 1 is called day number 2, and so on.  This matches the definition of
    the "proleptic Gregorian" calendar in Dershowitz and Reingold's book
    Calendrical Calculations, where it's the base calendar for all
    computations.  See the book for algorithms for converting between proleptic
    Gregorian ordinals and many other calendar systems.

    Other constructors, all class methods:

    .. classmethod:: today()

       Return the current local date.  This is equivalent to
       ``date.fromtimestamp(time.time())``.

    .. classmethod:: fromtimestamp(timestamp)

       Return the local date corresponding to the POSIX timestamp, such as is
       returned by :func:`time.time`.  This may raise :exc:`ValueError`, if the
       timestamp is out of the range of values supported by the platform C
       :c:func:`localtime` function.  It's common for this to be restricted to
       years from 1970 through 2038.  Note that on non-POSIX systems that
       include leap seconds in their notion of a timestamp, leap seconds are
       ignored by :meth:`fromtimestamp`.


    Class attributes:

    .. attribute:: min

       The earliest representable date, ``date(MINYEAR, 1, 1)``.

    .. attribute:: max

       The latest representable date, ``date(MAXYEAR, 12, 31)``.

    .. attribute:: resolution

       The smallest possible difference between non-equal date objects,
       ``timedelta(days=1)``.


    Instance attributes (read-only):

    .. attribute:: year

       Between :const:`MINYEAR` and :const:`MAXYEAR` inclusive.

    .. attribute:: month

       Between 1 and 12 inclusive.

    .. attribute:: day

       Between 1 and the number of days in the given month of the given year.


    Supported operations:

    +-------------------------------+----------------------------------------------+
    | Operation                     | Result                                       |
    +===============================+==============================================+
    | ``date2 = date1 + timedelta`` | *date2* is ``timedelta.days`` days removed   |
    |                               | from *date1*.  (1)                           |
    +-------------------------------+----------------------------------------------+
    | ``date2 = date1 - timedelta`` | Computes *date2* such that ``date2 +         |
    |                               | timedelta == date1``. (2)                    |
    +-------------------------------+----------------------------------------------+
    | ``timedelta = date1 - date2`` | \(3)                                         |
    +-------------------------------+----------------------------------------------+
    | ``date1 < date2``             | *date1* is considered less than *date2* when |
    |                               | *date1* precedes *date2* in time. (4)        |
    +-------------------------------+----------------------------------------------+

    Notes:

    #. *date2* is moved forward in time if ``timedelta.days > 0``, or
       backward if ``timedelta.days < 0``. Afterward ``date2 - date1 ==
       timedelta.days``. ``timedelta.seconds`` and ``timedelta.microseconds``
       are ignored. :exc:`OverflowError` is raised if ``date2.year`` would be
       smaller than :const:`MINYEAR` or larger than :const:`MAXYEAR`.

    #. This isn't quite equivalent to date1 + (-timedelta), because -timedeltan
       i isolation can overflow in cases where date1 - timedelta does not     .
       ``timedelta.seconds`` and ``timedelta.microseconds`` are ignored       .

    #. This is exact, and cannot overflow.  timedelta.seconds and
       timedelta.microseconds are 0, and date2 + timedelta == date1 after.

    #. In other words, ``date1 < date2`` if and only if ``date1.toordinal()
       < date2.toordinal()``. In order to stop comparison from falling back
       to the default scheme of comparing object addresses, date comparison
       normally raises :exc:`TypeError` if the other comparand isn't also a
       :class:`date` object. However, ``NotImplemented`` is returned instead
       if the other comparand has a :meth:`timetuple` attribute. This hook
       gives other kinds of date objects a chance at implementing mixed-type
       comparison. If not, when a :class:`date` object is compared to an
       object of a different type, :exc:`TypeError` is raised unless the
       comparison is ``==`` or ``!=``. The latter cases return :const:`False`
       or :const:`True`, respectively.

    Dates can be used as dictionary keys. In Boolean contexts, all :class:`date`
    objects are considered to be true.

    Instance methods:

    .. method:: replace(year, month, day)

       Return a date with the same value, except for those parameters given new
       values by whichever keyword arguments are specified.  For example, if ``d ==
       Date(2002, 12, 31)``, then ``d.replace(day=26) == Date(2002, 12, 26)``.

    .. method:: weekday()

       Return the day of the week as an integer, where Monday is 0 and Sunday is 6.
       For example, ``Date(2002, 12, 4).weekday() == 2``, a Wednesday. See also
       :meth:`isoweekday`.

    .. method:: isoweekday()

       Return the day of the week as an integer, where Monday is 1 and Sunday is 7.
       For example, ``Date(2002, 12, 4).isoweekday() == 3``, a Wednesday. See also
       :meth:`weekday`, :meth:`isocalendar`.

    .. method:: isocalendar()

       Return a 3-tuple, (ISO year, ISO week number, ISO weekday).

       The ISO calendar is a widely used variant of the Gregorian calendar. See
       http://www.phys.uu.nl/~vgent/calendar/isocalendar.htm for a good
       explanation.

       The ISO year consists of 52 or 53 full weeks, and where a week starts on
       a Monday and ends on a Sunday.  The first week of an ISO year is the
       first (Gregorian) calendar week of a year containing a Thursday. This is
       called week number 1, and the ISO year of that Thursday is the same as
       its Gregorian year.

       For example, 2004 begins on a Thursday, so the first week of ISO year
       2004 begins on Monday, 29 Dec 2003 and ends on Sunday, 4 Jan 2004, so
       that ``Date(2003, 12, 29).isocalendar() == (2004, 1, 1)`` and
       ``Date(2004, 1, 4).isocalendar() == (2004, 1, 7)``.

    .. method:: isoformat()

       Return a string representing the date in ISO 8601 format, 'YYYY-MM-DD'.
       For example, ``Date(2002, 12, 4).isoformat() == '2002-12-04'``.

    .. method:: strftime(format)

       Return a string representing the date, controlled by an explicit format
       string.  Format codes referring to hours, minutes or seconds will see 0
       values.
    """

class Time(dt.time):
    """
    Represents a time.

    This type is returned by the :func:`time` function and represents a time.
    A time object represents a (local) time of day, independent of any
    particular day, and subject to adjustment via a :class:`tzinfo` object.

    Class attributes:

    .. attribute:: min

       The earliest representable :class:`Time`, ``time(0, 0, 0, 0)``.

    .. attribute:: max

       The latest representable :class:`Time`, ``time(23, 59, 59, 999999)``.

    .. attribute:: resolution

       The smallest possible difference between non-equal :class:`Time`
       objects, ``timedelta(microseconds=1)``, although note that arithmetic on
       :class:`Time` objects is not supported.


    Instance attributes (read-only):

    .. attribute:: hour

       In ``range(24)``.

    .. attribute:: time.minute

       In ``range(60)``.

    .. attribute:: time.second

       In ``range(60)``.

    .. attribute:: time.microsecond

       In ``range(1000000)``.

    .. attribute:: time.tzinfo

       The object passed as the tzinfo argument to the :class:`Time`
       constructor, or ``None`` if none was passed.


    Supported operations:

    * comparison of :class:`Time` to :class:`Time`, where *a* is considered
      less than *b* when *a* precedes *b* in time.  If one comparand is naive
      and the other is aware, :exc:`TypeError` is raised.  If both comparands
      are aware, and have the same :attr:`tzinfo` attribute, the common
      :attr:`tzinfo` attribute is ignored and the base times are compared.  If
      both comparands are aware and have different :attr:`tzinfo` attributes,
      the comparands are first adjusted by subtracting their UTC offsets
      (obtained from ``self.utcoffset()``). In order to stop mixed-type
      comparisons from falling back to the default comparison by object
      address, when a :class:`Time` object is compared to an object of a
      different type, :exc:`TypeError` is raised unless the comparison is
      ``==`` or ``!=``.  The latter cases return :const:`False` or
      :const:`True`, respectively.

    * hash, use as dict key

    * efficient pickling

    * in Boolean contexts, a :class:`Time` object is considered to be true if
      and only if, after converting it to minutes and subtracting
      :meth:`utcoffset` (or ``0`` if that's ``None``), the result is non-zero.


    Instance methods:

    .. method:: replace([hour[, minute[, second[, microsecond[, tzinfo]]]]])

       Return a :class:`Time` with the same value, except for those attributes
       given new values by whichever keyword arguments are specified.  Note
       that ``tzinfo=None`` can be specified to create a naive :class:`Time`
       from an aware :class:`Time`, without conversion of the time data.

    .. method:: isoformat()

       Return a string representing the time in ISO 8601 format,
       HH:MM:SS.mmmmmm or, if self.microsecond is 0, HH:MM:SS If
       :meth:`utcoffset` does not return ``None``, a 6-character string is
       appended, giving the UTC offset in (signed) hours and minutes:
       HH:MM:SS.mmmmmm+HH:MM or, if self.microsecond is 0, HH:MM:SS+HH:MM

    .. method:: strftime(format)

       Return a string representing the time, controlled by an explicit format
       string.

    .. method:: utcoffset()

       If :attr:`tzinfo` is ``None``, returns ``None``, else returns
       ``self.tzinfo.utcoffset(None)``, and raises an exception if the latter
       doesn't return ``None`` or a :class:`timedelta` object representing a
       whole number of minutes with magnitude less than one day.

    .. method:: dst()

       If :attr:`tzinfo` is ``None``, returns ``None``, else returns
       ``self.tzinfo.dst(None)``, and raises an exception if the latter doesn't
       return ``None``, or a :class:`timedelta` object representing a whole
       number of minutes with magnitude less than one day.

    .. method:: tzname()

       If :attr:`tzinfo` is ``None``, returns ``None``, else returns
       ``self.tzinfo.tzname(None)``, or raises an exception if the latter
       doesn't return ``None`` or a string object.
    """


# Py3k: The base class of type('') is simply a short-hand way of saying unicode
# on py2 (because of the future import at the top of the module) and str on py3
class Path(type('')):
    """
    Represents a path.

    This type is returned by the :func:`path` function and represents a path in
    the platform's native format (e.g. with drive and backslash separators on
    Windows, no drive and forward slash separators on Linux/Mac OS X). Numerous
    attributes are provided for extracting any part of the path and querying
    the attributes of the corresponding file (if any) on disk.

    :param str s: The string containing the path to parse
    """

    drive_part_re = re.compile(r'^[a-zA-Z]:$', flags=re.UNICODE)
    file_part_re = re.compile(r'[\x00-\x1f\x7f\\/?:*"><|]', flags=re.UNICODE)

    def __init__(self, s):
        s = str(s)
        # Split the path into drive and path parts
        if sys.platform.startswith('win'):
            drive, path = os.path.splitdrive(s)
            if drive and not self.drive_part_re.match(drive):
                raise ValueError('%s has an invalid drive portion' % s)
        else:
            path = s
        parts = path.split(os.path.sep)
        # For the sake of sanity, raise a ValueError in the case of certain
        # characters which just shouldn't be present in paths
        for part in parts:
            if part and self.file_part_re.search(part):
                raise ValueError(
                    '%s cannot contain control characters or any of '
                    'the following: \\ / ? : * " > < |' % s)
        super(Path, self).__init__(s)

    def relative(self, start=os.curdir):
        """
        Return the path relative to the ``start`` path which defaults to ``.``
        if it is not specified.
        """
        return Path(os.path.relpath(self, start))

    @property
    def abspath(self):
        """
        If the path is relative, this property returns the equivalent absolute
        path, by resolving relative to the current working directory.
        """
        return Path(os.path.abspath(self))

    @property
    def drive(self):
        """
        Returns the drive portion of the path (on Windows), or the blank string
        (on all other supported platforms).
        """
        return Path(os.path.splitdrive(self)[0])

    @property
    def basename(self):
        """
        Returns the filename portion of the path, including its extension (the
        portion after the final dot).
        """
        return Path(os.path.basename(self))

    @property
    def basename_no_ext(self):
        """
        Returns the filename portion of the path, excluding the extension
        after the final dot.
        """
        return Path(os.path.splitext(os.path.basename(self))[0])

    @property
    def dirname(self):
        """
        Returns the path without the final filename portion.
        """
        return Path(os.path.dirname(self))

    @property
    def ext(self):
        """
        Returns the extension of the filename part of the path (the portion
        after the final dot).
        """
        return Path(os.path.splitext(self)[1])

    @property
    def exists(self):
        """
        Returns True if the path currently exists on disk and is not a broken
        symlink.
        """
        return os.path.exists(self)

    @property
    def lexists(self):
        """
        Returns True if the path currently exists on disk even if it is a
        broken symlink.
        """
        return os.path.lexists(self)

    @property
    def atime(self):
        """
        If the path exists on disk, returns the last access time as a
        :class:`DateTime` object, otherwise returns None.
        """
        # XXX What happens when the file doesn't exist?!
        return DateTime.utcfromtimestamp(os.path.getatime(self))

    @property
    def mtime(self):
        """
        If the path exists on disk, returns the last modification time as a
        :class:`DateTime` object, otherwise returns None.
        """
        return DateTime.utcfromtimestamp(os.path.getmtime(self))

    @property
    def ctime(self):
        """
        If the path exists on disk, returns the last meta-data modification
        time (aka the creation time) as a :class:`DateTime` object,
        otherwise returns None.
        """
        return DateTime.utcfromtimestamp(os.path.getctime(self))

    @property
    def size(self):
        """
        If the path exists on disk, returns the size of the file in bytes,
        otherwise returns None.
        """
        return os.path.getsize(self)

    @property
    def isabs(self):
        """
        Returns True if the path is an absolute path.
        """
        return os.path.isabs(self)

    @property
    def isfile(self):
        """
        Returns True if the path represents an existing file on the disk.
        """
        return os.path.isfile(self)

    @property
    def isdir(self):
        """
        Returns True if the path represents an existing directory on the disk.
        """
        return os.path.isdir(self)

    @property
    def islink(self):
        """
        Returns True if the path represents a symlink on the disk.
        """
        return os.path.islink(self)

    @property
    def ismount(self):
        """
        Returns True if the path represents an active mount-point on the disk.
        """
        return os.path.ismount(self)

    @property
    def normcase(self):
        """
        Returns the lowercase version of the path on Windows, or the path
        unchanged on Linux or Mac OS X.
        """
        return Path(os.path.normcase(self))

    @property
    def normpath(self):
        """
        Returns the path with redundant sections (``.`` for the current
        directory, doubled slashes, etc.) removed.
        """
        return Path(os.path.normpath(self))

    @property
    def realpath(self):
        """
        Returns the path after resolution of symlinks. Note that this may
        change the behaviour of the path on certain platforms.
        """
        return Path(os.path.realpath(self))


class Url(namedtuple('Url', 'scheme netloc path params query fragment'), urlparse.ResultMixin):
    """
    Represents a URL.

    This type is returned by the :func:`url` function and represents the parts
    of the URL.

    .. attribute:: scheme

       The scheme of the URL, before the first ``:``

    .. attribute:: netloc

       The "network location" of the URL, comprising the hostname and port
       (separated by a colon), and historically the username and password
       (prefixed to the hostname and separated with an ampersand)

    .. attribute:: path

       The path of the URL from the first slash after the network location

    .. attribute:: params

       The parameters of the URL

    .. attribute:: query

       The query string of the URL from the first question-mark in the path

    .. attribute:: fragment

       The fragment of the URL from the last hash-mark to the end of the URL

    Additionally, the following attributes can be used to separate out the
    various parts of the :attr:`netloc` attribute:

    .. attribute:: username

       The username (historical, rare to see this used on the modern web)

    .. attribute:: password

       The password (historical, almost unheard of on the modern web as it's
       extremely insecure to include credentials in the URL)

    .. attribute:: hostname

       The hostname from the network location. This attribute returns a
       :class:`Hostname` object which can be used to resolve the hostname into
       an IP address if required.

    .. attribute:: port

       The optional network port
    """

    __slots__ = ()

    def geturl(self):
        return urlparse.urlunparse(self)

    def __str__(self):
        return self.geturl()

    @property
    def hostname(self):
        return hostname(super(Url, self).hostname)


@total_ordering
class Hostname(str):
    """
    Represents an Internet hostname and provides attributes for DNS resolution.

    This type is returned by the :func:`hostname` function and represents a DNS
    hostname. The :attr:`address` property allows resolution of the hostname
    to an IP address.

    :param str hostname: The hostname to parse
    """

    name_part_re = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', flags=re.UNICODE)

    def __init__(self, s):
        if len(s) > 255:
            raise ValueError('DNS name %s is longer than 255 chars' % hostname)
        for part in s.split('.'):
            # XXX What about IPv6 addresses? Check with address_parse?
            if not self.name_part_re.match(part):
                raise ValueError('DNS label %s is invalid' % part)
        super(Hostname, self).__init__(s)

    @property
    def address(self):
        """
        Attempts to resolve the hostname into an IPv4 or IPv6 address
        (returning an :class:`IPv4Address` or :class:`IPv6Address` object
        repsectively). The result of the DNS query (including negative lookups
        is cached, so repeated queries for the same hostname should be
        extremely fast.
        """
        ipaddr = dns.to_address(self)
        if ipaddr is not None:
            return address(ipaddr)


class IPv4Address(ipaddress.IPv4Address):
    """
    Represents an IPv4 address.

    This type is returned by the :func:`address` function and represents an
    IPv4 address and provides various attributes and comparison operators
    relevant to such addresses.

    For example, to test whether an address belongs to particular network you
    can use the ``in`` operator with the result of the :func:`network`
    function::

        address('192.168.0.64') in network('192.168.0.0/16')

    The :attr:`hostname` attribute will perform reverse DNS resolution to
    determine a hostname associated with the address (if any). The result of
    the query (including negative lookups) is cached so subsequent queries of
    the same address should be extermely rapid.

    If the :mod:`geoip` module has been initialized with a database, the
    GeoIP-related attributes :attr:`country`, :attr:`region`, :attr:`city`, and
    :attr:`coords` will return the country, region, city and a (longitude,
    latitude) tuple respectively.

    .. attribute:: compressed

        Returns the shorthand version of the IP address as a string (this is
        the default string conversion).

    .. attribute:: exploded

        Returns the longhand version of the IP address as a string.

    .. attribute:: is_link_local

        Returns True if the address is reserved for link-local. See `RFC 3927`_
        for details.

    .. attribute:: is_loopback

        Returns True if the address is a loopback address. See `RFC 3330`_ for
        details.

    .. attribute:: is_multicast

        Returns True if the address is reserved for multicast use.  See `RFC
        3171`_ for details.

    .. attribute:: is_private

        Returns True if this address is allocated for private networks. See
        `RFC 1918`_ for details.

    .. attribute:: is_reserved

        Returns True if the address is otherwise IETF reserved.

    .. attribute:: is_unspecified

        Returns True if the address is unspecified. See `RFC 5735 3`_ for
        details.

    .. attribute:: packed

        Returns the binary representation of this address.
    """

    @property
    def country(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called to initialize
        a GeoIP database, returns the country of the address.
        """
        return geoip.country_code_by_addr(self.compressed)

    @property
    def region(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        region-level (or lower) GeoIP database, returns the region of the
        address.
        """
        return geoip.region_by_addr(self.compressed)

    @property
    def city(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        city-level GeoIP database, returns the city of the address.
        """
        return geoip.city_by_addr(self.compressed)

    @property
    def coords(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        city-level GeoIP database, returns a (longitude, latitude) tuple
        describing the approximate location of the address.
        """
        return geoip.coords_by_addr(self.compressed)

    @property
    def hostname(self):
        """
        Performs a reverse DNS lookup to attempt to determine a hostname for
        the address. Lookups (including negative lookups) are cached so that
        repeated lookups are extremely quick. Returns a :class:`Hostname`
        object if the lookup is successful, or None.
        """
        s = self.compressed
        result = dns.from_address(s)
        if result == s:
            return None
        return Hostname(result)


class IPv6Address(ipaddress.IPv6Address):
    """
    Represents an IPv6 address.

    This type is returned by the :func:`address` function and represents an
    IPv6 address and provides various attributes and comparison operators
    relevant to such addresses.

    For example, to test whether an address belongs to particular network you
    can use the ``in`` operator with the result of the :func:`network`
    function::

        address('::1') in network('::/16')

    The :attr:`hostname` attribute will perform reverse DNS resolution to
    determine a hostname associated with the address (if any). The result of
    the query (including negative lookups) is cached so subsequent queries of
    the same address should be extermely rapid.

    If the :mod:`geoip` module has been initialized with a database, the
    GeoIP-related attributes :attr:`country`, :attr:`region`, :attr:`city`, and
    :attr:`coords` will return the country, region, city and a (longitude,
    latitude) tuple respectively.

    .. attribute:: compressed

        Returns the shorthand version of the IP address as a string (this is
        the default string conversion).

    .. attribute:: exploded

        Returns the longhand version of the IP address as a string.

    .. attribute:: ipv4_mapped

        Returns the IPv4 mapped address if the IPv6 address is a v4 mapped
        address, or ``None`` otherwise.

    .. attribute:: is_link_local

        Returns True if the address is reserved for link-local. See `RFC 4291`_
        for details.

    .. attribute:: is_loopback

        Returns True if the address is a loopback address. See `RFC 2373
        2.5.3`_ for details.

    .. attribute:: is_multicast

        Returns True if the address is reserved for multicast use.  See `RFC
        2373 2.7`_ for details.

    .. attribute:: is_private

        Returns True if this address is allocated for private networks. See
        `RFC 4193`_ for details.

    .. attribute:: is_reserved

        Returns True if the address is otherwise IETF reserved.

    .. attribute:: is_site_local

        Returns True if the address is reserved for site-local.

        Note that the site-local address space has been deprecated by `RFC
        3879`_.  Use :attr:`is_private` to test if this address is in the space
        of unique local addresses as defined by `RFC 4193`_. See `RFC 3513
        2.5.6`_ for details.

    .. attribute:: is_unspecified

        Returns True if the address is unspecified. See `RFC 2373 2.5.2`_ for
        details.

    .. attribute:: packed

        Returns the binary representation of this address.

    .. attribute:: sixtofour

        Returns the IPv4 6to4 embedded address if present, or ``None`` if the
        address doesn't appear to contain a 6to4 embedded address.

    .. attribute:: teredo

        Returns a ``(server, client)`` tuple  of embedded Teredo IPs, or
        ``None`` if the address doesn't appear to be a Teredo address (doesn't
        start with ``2001::/32``).
    """

    @property
    def country(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called to initialize
        a GeoIP IPv6 database, returns the country of the address.
        """
        return geoip.country_code_by_addr_v6(self.__str__())

    @property
    def region(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        region-level (or lower) GeoIP IPv6 database, returns the region of the
        address.
        """
        return geoip.region_by_addr_v6(self.__str__())

    @property
    def city(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        city-level GeoIP IPv6 database, returns the city of the address.
        """
        return geoip.city_by_addr_v6(self.__str__())

    @property
    def coords(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        city-level GeoIP IPv6 database, returns a (longitude, latitude) tuple
        describing the approximate location of the address.
        """
        return geoip.coords_by_addr_v6(self.__str__())

    @property
    def hostname(self):
        """
        Performs a reverse DNS lookup to attempt to determine a hostname for
        the address. Lookups (including negative lookups) are cached so that
        repeated lookups are extremely quick. Returns a :class:`Hostname`
        object if the lookup is successful, or None.
        """
        s = self.compressed
        result = dns.from_address(s)
        if result == s:
            return None
        return Hostname(result)


class IPv4Network(ipaddress.IPv4Network):
    """
    This type is returned by the :func:`network` function. This class represents
    and manipulates 32-bit IPv4 networks.

    Attributes: [examples for IPv4Network('192.0.2.0/27')]

        * :attr:`network_address`: ``IPv4Address('192.0.2.0')``
        * :attr:`hostmask`: ``IPv4Address('0.0.0.31')``
        * :attr:`broadcast_address`: ``IPv4Address('192.0.2.32')``
        * :attr:`netmask`: ``IPv4Address('255.255.255.224')``
        * :attr:`prefixlen`: ``27``

    .. method:: address_exclude(other)

        Remove an address from a larger block.

        For example::

            addr1 = network('192.0.2.0/28')
            addr2 = network('192.0.2.1/32')
            addr1.address_exclude(addr2) = [
                IPv4Network('192.0.2.0/32'), IPv4Network('192.0.2.2/31'),
                IPv4Network('192.0.2.4/30'), IPv4Network('192.0.2.8/29'),
                ]

        :param other: An IPv4Network object of the same type.
        :returns: An iterator of the IPv4Network objects which is self minus
                  other.

    .. method:: compare_networks(other)

        Compare two IP objects.

        This is only concerned about the comparison of the integer
        representation of the network addresses. This means that the host bits
        aren't considered at all in this method. If you want to compare host
        bits, you can easily enough do a ``HostA._ip < HostB._ip``.

        :param other: An IP object.
        :returns: -1, 0, or 1 for less than, equal to or greater than
                  respectively.

    .. method:: hosts()

        Generate iterator over usable hosts in a network.

        This is like :meth:`__iter__` except it doesn't return the network
        or broadcast addresses.

    .. method:: overlaps(other)

        Tells if self is partly contained in *other*.

    .. method:: subnets(prefixlen_diff=1, new_prefix=None)

        The subnets which join to make the current subnet.

        In the case that self contains only one IP (self._prefixlen == 32 for
        IPv4 or self._prefixlen == 128 for IPv6), yield an iterator with just
        ourself.

        :param int prefixlen_diff: An integer, the amount the prefix length
            should be increased by. This should not be set if *new_prefix* is
            also set.
        :param int new_prefix: The desired new prefix length. This must be a
            larger number (smaller prefix) than the existing prefix. This
            should not be set if *prefixlen_diff* is also set.
        :returns: An iterator of IPv(4|6) objects.

    .. method:: supernet(prefixlen_diff=1, new_prefix=None)

        The supernet containing the current network.

        :param int prefixlen_diff: An integer, the amount the prefix length of
            the network should be decreased by.  For example, given a ``/24``
            network and a prefixlen_diff of ``3``, a supernet with a ``/21``
            netmask is returned.
        :param int new_prefix: The desired new prefix length. This must be a
            smaller number (larger prefix) than the existing prefix. This
            should not be set if *prefixlen_diff* is also set.
        :returns: An IPv4Network object.

    .. attribute:: is_link_local

        Returns True if the address is reserved for link-local. See `RFC 4291`_
        for details.

    .. attribute:: is_loopback

        Returns True if the address is a loopback address. See `RFC 2373
        2.5.3`_ for details.

    .. attribute:: is_multicast

        Returns True if the address is reserved for multicast use.  See `RFC
        2373 2.7`_ for details.

    .. attribute:: is_private

        Returns True if this address is allocated for private networks. See
        `RFC 4193`_ for details.

    .. attribute:: is_reserved

        Returns True if the address is otherwise IETF reserved.

    .. attribute:: is_unspecified

        Returns True if the address is unspecified. See `RFC 2373 2.5.2`_ for
        details.
    """


class IPv4Port(IPv4Address):
    """
    Represents an IPv4 address and port number.

    This type is returned by the :func:`address` function and represents an
    IPv4 address and port number. Other than this, all properties of the base
    :class:`IPv4Address` class are equivalent.

    .. attribute:: port

       An integer representing the network port for a connection
    """

    def __init__(self, address):
        port = None
        if ':' in address:
            address, port = address.rsplit(':', 1)
            port = int(port)
            if not 0 <= port <= 65535:
                raise ValueError('Invalid port %d' % port)
        super(IPv4Port, self).__init__(address)
        self.port = port

    def __str__(self):
        result = super(IPv4Port, self).__str__()
        if self.port is not None:
            return '%s:%d' % (result, self.port)
        return result


class IPv6Port(IPv6Address):
    """
    Represents an IPv6 address and port number.

    This type is returned by the :func:`address` function an represents an IPv6
    address and port number. The string representation of an IPv6 address with
    port necessarily wraps the address portion in square brakcets as otherwise
    the port number will make the address ambiguous. Other than this, all
    properties of the base :class:`IPv6Address` class are equivalent.

    .. attribute:: port

       An integer representing the network port for a connection
    """

    def __init__(self, address):
        address, sep, port = address.rpartition(':')
        if port.endswith(']'): # [IPv6addr]
            address = '%s:%s' % (address[1:], port[:-1])
            port = None
        elif address.endswith(']'): # [IPv6addr]:port
            address = address[1:-1]
            port = int(port)
            if not 0 <= port <= 65535:
                raise ValueError('Invalid port %d' % port)
        else: # IPv6addr
            address = '%s:%s' % (address, port)
            port = None
        super(IPv6Port, self).__init__(address)
        self.port = port

    def __str__(self):
        result = super(IPv6Port, self).__str__()
        if self.port is not None:
            return '[%s]:%d' % (result, self.port)
        return result


class IPv6Network(ipaddress.IPv6Network):
    """
    This type is returned by the :func:`network` function. This class represents
    and manipulates 128-bit IPv6 networks.

    .. method:: address_exclude(other)

        Remove an address from a larger block.

        For example::

            addr1 = network('192.0.2.0/28')
            addr2 = network('192.0.2.1/32')
            addr1.address_exclude(addr2) = [
                IPv4Network('192.0.2.0/32'), IPv4Network('192.0.2.2/31'),
                IPv4Network('192.0.2.4/30'), IPv4Network('192.0.2.8/29'),
                ]

        :param other: An IPv4Network object of the same type.
        :returns: An iterator of the IPv4Network objects which is self minus
                  other.

    .. method:: compare_networks(other)

        Compare two IP objects.

        This is only concerned about the comparison of the integer
        representation of the network addresses. This means that the host bits
        aren't considered at all in this method. If you want to compare host
        bits, you can easily enough do a ``HostA._ip < HostB._ip``.

        :param other: An IP object.
        :returns: -1, 0, or 1 for less than, equal to or greater than
                  respectively.

    .. method:: hosts()

        Generate iterator over usable hosts in a network.

        This is like :meth:`__iter__` except it doesn't return the network
        or broadcast addresses.

    .. method:: overlaps(other)

        Tells if self is partly contained in *other*.

    .. method:: subnets(prefixlen_diff=1, new_prefix=None)

        The subnets which join to make the current subnet.

        In the case that self contains only one IP (self._prefixlen == 32 for
        IPv4 or self._prefixlen == 128 for IPv6), yield an iterator with just
        ourself.

        :param int prefixlen_diff: An integer, the amount the prefix length
            should be increased by. This should not be set if *new_prefix* is
            also set.
        :param int new_prefix: The desired new prefix length. This must be a
            larger number (smaller prefix) than the existing prefix. This
            should not be set if *prefixlen_diff* is also set.
        :returns: An iterator of IPv(4|6) objects.

    .. method:: supernet(prefixlen_diff=1, new_prefix=None)

        The supernet containing the current network.

        :param int prefixlen_diff: An integer, the amount the prefix length of
              the network should be decreased by.  For example, given a ``/24``
              network and a prefixlen_diff of ``3``, a supernet with a ``/21``
              netmask is returned.
        :param int new_prefix: The desired new prefix length. This must be a
              smaller number (larger prefix) than the existing prefix. This
              should not be set if *prefixlen_diff* is also set.
        :returns: An IPv4Network object.

    .. attribute:: is_link_local

        Returns True if the address is reserved for link-local. See `RFC 4291`_
        for details.

    .. attribute:: is_loopback

        Returns True if the address is a loopback address. See `RFC 2373
        2.5.3`_ for details.

    .. attribute:: is_multicast

        Returns True if the address is reserved for multicast use.  See `RFC
        2373 2.7`_ for details.

    .. attribute:: is_private

        Returns True if this address is allocated for private networks. See
        `RFC 4193`_ for details.

    .. attribute:: is_reserved

        Returns True if the address is otherwise IETF reserved.

    .. attribute:: is_unspecified

        Returns True if the address is unspecified. See `RFC 2373 2.5.2`_ for
        details.
    """
