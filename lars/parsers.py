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
This module provides common parsing regular expressions and functinos which
occur across multiple log formats. End users should never need to reference
this module.
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from lars import datatypes as dt

str = type('')  # pylint: disable=redefined-builtin,invalid-name


# Note - we do NOT try and validate URLs with this regex (as to do so is
# incredibly complicated and much better left to a function), merely perform
# some rudimentary extraction. The complex stuff below is derived from RFC3986
# appendix B.

_URL = r'([^:/?#\s]+:)?(//[^/?#\s]*)?[^?#\s]*(\?[^#\s]*)?(#\S*)?'

# The following regex for paths is ridiculously lax (and practically guaranteed
# to make any undelimited regex containing it ambiguous. Unfortunately there's
# not much we can do about this as none of the log formats escape filename
# fields! In other words, it's down to users not to use nutty filenames and to
# specify log formats containing sensible delims around any paths

_PATH = r'([^\x00-\x1f\x7f]*)'

# Extension methods can potentially be used, hence this regex just matches the
# "token" production in RFC2616 2.2. Note that this regex cannot match "-"
# because a method *within a request* cannot be unknown (see REQUEST below for
# more information).

_METHOD = r'[^\x00-\x1f\x7f(){}<>[\]@,;:\\"/?= \t]+'

# Same goes for HTTP PROTOCOL - can never be "-".

_PROTOCOL = r'HTTP/\d+\.\d+'

# In the following regexes, there must be a single group which covers the
# entire match. The group must be a named group with the name %(name)s, which
# will be substituted for the Python-ified field name in the regex constructed
# for row matching. Note that most regexes also match "-" which is used almost
# universally in web-logging systems to indicate a NULL value.

INTEGER = r'(?P<%(name)s>-|\d+)'
FIXED = r'(?P<%(name)s>-|\d+(\.\d*)?)'
DATE_ISO = r'(?P<%(name)s>-|\d{4}-\d{2}-\d{2})'
TIME_ISO = r'(?P<%(name)s>-|\d{2}:\d{2}:\d{2})'

# The reason for the empty "-" production appearing on the right is due to an
# issue with disjuncts in Perl-style regex implementations, see
# <http://lingpipe-blog.com/2008/05/07/tokenization-vs-eager-regular-expressions/>
#
# Note that the empty production "-" is possible for METHOD, PROTOCOL and
# REQUEST (e.g. due to request timeout), however the method cannot be empty
# ("-") unless the *entire* request is empty hence why the empty match "-" is
# only introduced here and not in the regexes above.

URL = r'(?P<%%(name)s>%s|-)' % _URL
PATH = r'(?P<%%(name)s>%s|-)' % _PATH
METHOD = r'(?P<%%(name)s>%s|-)' % _METHOD
PROTOCOL = r'(?P<%%(name)s>%s|-)' % _PROTOCOL
REQUEST = r'(?P<%%(name)s>%s %s %s|-)' % (_METHOD, _URL, _PROTOCOL)

# Doing DNS (or IP) validation is extremely hard to do properly with regexes so
# here we use a trivial regex to pull out a string containing the right
# alphabet and do validation in a function

HOSTNAME = r'(?P<%(name)s>-|[a-zA-Z0-9:.-]+)'

# Again, regex validation of IP addresses is extremely hard to do properly so
# we perform validation later in a function

ADDRESS = r'(?P<%(name)s>-|[0-9]+(\.[0-9]+){3}|[0-9a-fA-F:]+)'
ADDRESS_PORT = (
    r'(?P<%(name)s>'
    r'-|([0-9]+(\.[0-9]+){3}|\[[0-9a-fA-F:]+\])(:[0-9]{1,5})?)'
)


def request_parse(s):
    """
    Parse an HTTP request line in a log file.

    This is a basic function that simply returns the three components of a
    request line (method, url, and protocol) as tuple. If URL is "*" (denoting
    a missing URL for methods which do not require one, like OPTIONS), the
    middle element of the returned tuple will be None.

    :param str s: The string containing the request line to parse
    :returns: A :class:`~lars.datatypes.Request` tuple representing the
              request line
    """
    return dt.request(s) if s != '-' else None


def url_parse(s):
    """
    Parse a URL string in a log file.

    This is a variant on the standard Python urlparse.urlparse function. The
    result type has been extended to include a
    :meth:`~lars.datatypes.Url.__str__` method which outputs the
    reconstructed URL, and to have specialized hostname and path properties
    which return enhanced objects instead of simple strings.

    :param str s: The string containing the URI to parse
    :returns: A :class:`~lars.datatypes.Url` tuple representing the URL
    """
    return dt.url(s) if s not in ('-', '') else None


def path_parse(s):
    """
    Parse a POSIX-style (slash separated) path string in a log file.

    :param str s: The srting containing the POSIX-style path to parse
    :returns: A :class:`~lars.datatypes.Path` object representing the path
    """
    return dt.path(s) if s != '-' else None


def int_parse(s):
    """
    Parse an integer string in a log file.

    This is a simple variant on int() that returns None in the case of a single
    dash being passed to s.

    :param str s: The string containing the integer number to parse
    :returns: An int value
    """
    return int(s) if s != '-' else None


def fixed_parse(s):
    """
    Parse an floating point string in a log file.

    This is a simple variant on float() that returns None in the case of a
    single dash being passed to s.

    :param str s: The string containing the floating point number to parse
    :returns: An float value
    """
    return float(s) if s != '-' else None


def date_parse(s, format='%Y-%m-%d'):
    """
    Parse a date string in a log file.

    :param str s: The string containing the date to parse
    :param str format: The optional strftime(3) format string
    :returns: A :class:`~lars.datatypes.Date` object representing the date
    """
    # pylint: disable=redefined-builtin
    return dt.date(s, format) if s != '-' else None


def time_parse(s, format='%H:%M:%S'):
    """
    Parse a time string in a IIS extended log format file.

    :param str s: The string containing the time to parse (HH:MM:SS format)
    :param str format: The optional strftime(3) format string
    :returns: A :class:`~lars.datatypes.Time` object representing the time
    """
    # pylint: disable=redefined-builtin
    return dt.time(s, format) if s != '-' else None


def hostname_parse(s):
    """
    Parse a DNS name in a log format.

    :param str s: The string containing the DNS name to parse
    :returns: A :class:`~lars.datatypes.Hostname` value
    """
    return dt.hostname(s) if s != '-' else None


def address_parse(s):
    """
    Parse an IPv4 or IPv6 address (and optional port) in a log file.

    :param str s: The string containing the address to parse
    :returns: A :class:`~lars.datatypes.IPv4Address` value
    """
    return dt.address(s) if s != '-' else None
