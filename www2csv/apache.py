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

"""
This module provides a wrapper for Apache log files, typically in common or
combined format (but technically any Apache format which is can be
unambiguously parsed with regexes).

The :class:`ApacheSource` class is the major element that this module exports;
this is the class which wraps a file-like object containing a common, combined,
or otherwise Apache formatted log file and yields rows from it as tuples.


Classes
=======

.. autoclass:: ApacheSource
   :members:


Data
====

.. data:: COMMON

    This string contains the Apache LogFormat string for the common log format
    (sometimes called the CLF). This is the default format for the
    :class:`ApacheSource` class.

.. data:: COMMON_VHOST

    This string contains the Apache LogFormat strnig for the common log format
    with an additional virtual-host specification at the beginning of the
    string. This is a typical configuration used by several distributions of
    Apache which are configured with virtualhosts by default.

.. data:: COMBINED

    This string contains the Apache LogFormat string for the NCSA
    combined/extended log format. This is a popular variant that many server
    administrators use as it combines the :data:`COMMON` format with
    :data:`REFERER` and :data:`USER_AGENT` formats.

.. data:: REFERER

    This string contains the (rudimentary) referer log format which is
    typically used in conjunction with the :data:`COMMON` format.

.. data:: USER_AGENT

    This string contains the (rudimentary) user-agent log format which is
    typically used in conjunction with the :data:`COMMON` format.


Exceptions
==========

.. autoclass:: ApacheError
   :members:

.. autoexception:: ApacheWarning


Examples
========

A typical usage of this class is as follows::

    import io
    from www2csv import apache, csv

    with io.open('/var/log/apache2/access.log', 'rb') as infile:
        with io.open('access.csv', 'wb') as outfile:
            with apache.ApacheSource(infile) as source:
                with csv.CSVTarget(outfile) as target:
                    for row in source:
                        target.write(row)

.. _Custom Log Formats: http://httpd.apache.org/docs/2.2/mod/mod_log_config.html#formats
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import re
import warnings
import logging
from urllib import unquote_plus

from www2csv.datatypes import date, time, datetime,url, address, hostname, row


# Make Py2 str same as Py3
str = type('')


__all__ = [
    'ApacheSource',
    'ApacheError',
    'ApacheWarning',
    ]


class ApacheError(StandardError):
    """
    Base class for ApacheSource errors.

    Exceptions of this class take the optional arguments line_number and line
    for specifying the index and content of the line that caused the error
    respectively. If specified, the :meth:`__str__` method is overridden to
    include the line number in the error message.

    :param str message: The error message
    :param int line_number: The 1-based index of the line that caused the error
    :param str line: The content of the line that caused the error
    """
    def __init__(self, message, line_number=None, line=None):
        self.line_number = line_number
        self.line = line
        super(ApacheError, self).__init__(message)

    def __str__(self):
        result = super(ApacheError, self).__str__()
        if self.line_number:
            result = 'Line %d: %s' % (self.line_number, result)
        return result


class ApacheWarning(Warning):
    """
    Raised when an error is encountered in parsing a log row.
    """


class ApacheSource(object):
    """
    Wraps a steam containing a Apache formatted log file.

    This wrapper converts a stream containing an Apache log file into an
    iterable which yields tuples. Each tuple is a namedtuple instance with the
    fieldnames of the tuple being derived from the following mapping of Apache
    format strings:

    ============= ==================
    Format String Field Name
    ============= ==================
    %a            remote_ip
    %A            local_ip
    %B            size
    %b            size_clf
    %{Foobar}C    cookie_Foobar (1)
    %D            time_taken_ms
    %{FOOBAR}e    env_FOOBAR
    %f            filename
    %h            remote_host
    %H            protocol
    %{Foobar}i    req_Foobar
    %k            keepalive
    %l            ident
    %m            method
    %{Foobar}n    note_Foobar
    %{Foobar}o    resp_Foobar
    %p            port
    %{canonical}p port
    %{local}p     local_port
    %{remote}p    remote_port
    %P            pid
    %{pid}P       pid
    %{tid}P       tid
    %{hextid}P    hextid
    %q            url_query
    %r            request
    %R            handler
    %s            status
    %t            time
    %{format}t    time
    %T            time_taken
    %u            remote_user
    %U            url_stem
    %v            server_name
    %V            canonical_name
    %X            connection_status
    %I            bytes_received
    %O            bytes_sent
    ============= ==================

    Notes:

    (1)
        Any characters in the field-name which are invalid in a Python
        identifier are converted to underscore, e.g. %{foo-bar}C becomes
        ``"cookie_foo_bar"``.

    .. warning::

        The wrapper will only operate on LogFormat specifications that can be
        unambiguously parsed with a regular expression. In particular, this
        means that if a field can contain whitespace it must be surrounded by
        characters that it cannot legitimately contain (or cannot contain
        unescaped versions of). Typically double-quotes are used as Apache
        (from version 2.0.46) escapes double-quotes within %r, %i, and %o.
        See Apache's `Custom Log Formats`_ documentation for full details.

    :param source: A file-like object containing the source stream
    :param format: Defaults to :data:`COMMON` but can be set to any valid
                   Apache LogFormat string
    """

    def __init__(self, source, format=COMMON):
        pass
