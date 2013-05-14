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
import functools

from www2csv import parsers, datatypes as dt
from www2csv.strptime import TimeRE, _strptime_datetime


# Make Py2 str same as Py3
str = type('')


__all__ = [
    'ApacheSource',
    'ApacheError',
    'ApacheWarning',
    'COMMON',
    'COMMON_VHOST',
    'COMBINED',
    'REFERER',
    'USER_AGENT',
    ]


# Common Apache LogFormat strings
COMMON = '%h %l %u %t "%r" %>s %b'
COMMON_VHOST = '%v %h %l %u %t "%r" %>s %b'
COMBINED = '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"'
REFERER = '%{Referer} -> %U'
USER_AGENT = '%{User-agent}i'

# Standard Apache time format
APACHE_TIME = '[%d/%b/%Y:%H:%M:%S %z]'


# We need a reference to the "standard English" locale for parsing the
# unadorned %t time format in Apache log files. The only truly safe way of
# doing this (given that an English locale may not even be installed on the
# machine) is to hard-code a fake one. The following is derived from a machine
# with the locale explicitly set to en_US (presumably what Apache means they
# refer to "standard English"...):
class EnglishLocaleTime(object):
    def __init__(self):
        self.a_month = [
            '',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
            ]
        self.a_weekday = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        self.am_pm = ['am', 'pm']
        self.f_month = [
            '',
            'january', 'february', 'march',
            'april',   'may',      'june',
            'july',    'august',   'september',
            'october', 'november', 'december',
            ]
        self.f_weekday = [
            'monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'sunday',
            ]
        self.lang = ('en_US', 'UTF-8')
        self.LC_date = '%m/%d/%Y'
        self.LC_date_time = '%a %d %b %Y %I:%M:%S %p %Z'
        self.LC_time = '%I:%M:%S %p'
        self.timezone = (frozenset(('utc', 'gmt')), frozenset('bst'))


_string_parse_re = re.compile(r'\\(x[0-9a-fA-F]{2}|[^x])')
def string_parse(s):
    """
    Parse a string in an Apache log file.

    This function unescapes backslash-prefixed escape sequences. Specifically,
    ``\\xhh`` hex-sequences, and the standard C whitespace sequences of
    ``\\n``, ``\\t``, and ``\\f``. Anything else prefixed with a backslash
    (such as a double-quote or another backslash) has the leading backslash
    removed but is left otherwise unchanged.

    :param str s: The string to parse
    :returns: The decoded string
    """
    if s == '-':
        return None
    whitespace = {
        '\\n': '\n',
        '\\t': '\t',
        '\\f': '\f',
        }
    def unescape(match):
        match = match.group(0)
        if match.startswith('\\x'):
            return chr(int(match[2:4], base=16))
        else:
            return whitespace.get(match, match[-1])
    return _string_parse_re.sub(unescape, s)


def time_parse(s, fmt):
    """
    Parse a time value in an Apache log file.

    Note that this function is not intended to be used on its own, but rather
    to be treated as the template for an implementation derived with the
    :func:`~functools.partial` function from functools.

    :param str s: The string containing the time to parse
    :param str fmt: The strptime format the string must conform to
    :returns: A naive :class:`~www2csv.datatypes.DateTime` object
    """
    d = _strptime_datetime(dt.DateTime, s, fmt)
    return d.replace(tzinfo=None) - d.utcoffset()


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
    iterable which yields tuples. Each tuple has fieldnames derived from the
    following mapping of Apache format strings (which occur in the optional
    *log_format* parameter):

    ============= ==================
    Format String Field Name
    ============= ==================
    %a            remote_ip
    %A            local_ip
    %B            size
    %b            size_clf
    %{Foobar}C    cookie_Foobar (1)
    %D            time_taken_ms
    %{FOOBAR}e    env_FOOBAR (1)
    %f            filename
    %h            remote_host
    %H            protocol
    %{Foobar}i    req_Foobar (1)
    %k            keepalive
    %l            ident
    %m            method
    %{Foobar}n    note_Foobar (1)
    %{Foobar}o    resp_Foobar (1)
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
        identifier are converted to underscore, e.g. ``%{foo-bar}C`` becomes
        ``"cookie_foo_bar"``.

    .. warning::

        The wrapper will only operate on *log_format* specifications that can
        be unambiguously parsed with a regular expression. In particular, this
        means that if a field can contain whitespace it must be surrounded by
        characters that it cannot legitimately contain (or cannot contain
        unescaped versions of). Typically double-quotes are used as Apache
        (from version 2.0.46) escapes double-quotes within ``%r``, ``%i``, and
        ``%o``.  See Apache's `Custom Log Formats`_ documentation for full
        details.

    :param source: A file-like object containing the source stream
    :param str format: Defaults to :data:`COMMON` but can be set to any valid
                   Apache LogFormat string
    :param bool localized_time: If False, assume customized ``%t`` format
                   strings use English strings for months and weekdays.
                   Defaults to True (assume localized strings)
    """

    def __init__(self, source, log_format=COMMON, localized_time=True):
        self.source = source
        self.log_format = log_format
        self._time_re = TimeRE()
        self._parse_log_format()
        self._row_pattern = None
        self._row_funcs = None
        self._row_type = None

    # This regex is used for extracting the format specifications from an
    # Apache LogFormat directive. See [1] for full details of the syntax.
    #
    # [1] http://httpd.apache.org/docs/2.2/mod/mod_log_config.html#formats
    FIELD_RE1 = re.compile(
        # Main capturing group to ensure re.split() returns everything
        r'(%'
            # Optional status code filter with optional negation
            r'(?:!?\d{3}(?:,\d{3})*)?'
            # Optional request original/final modifier
            r'[<>]?'
            # Format specification group
            r'(?:'
                # Simple specs
                r'[aAbBDfhHklmpPqrRstTuUvVXIO]|'
                # Header/env/pid specs
                r'\{[a-zA-Z][a-zA-Z0-9_-]*\}[einopP]|'
                # Cookie spec (any HTTP token is permitted as a name)
                r'\{[^\x00-\x1F\x7F(){}<>[\]@,;:\\"/?= \t]+\}C|'
                # Time spec
                r'\{[^}]*\}t'
            r')'
        r')'
        )

    # This regular expression is used to parse a format specification after
    # extraction from a LogFormat string. It is effectively a simplified form
    # of FIELD_RE1 above with anchors and groups to capture the useful
    # portions of the spec (basically the formatting character and any {field}
    # before it.
    FIELD_RE2 = re.compile(
        r'^%'
        # Optional status code - non-capturing group as we don't want this
        r'(?:!?\d{3}(?:,\d{3})*)?'
        # Optional request modifier - no group as we don't want this either
        r'[<>]?'
        # Optional {field} group
        r'(?P<field>{[^}]*})?'
        # Specification suffix letter
        r'(?P<suffix>[aAbBCDefhHiklmnopPqrRstTuUvVXIO])'
        r'$'
        )

    # This mapping relates format specifications to field names and types, for
    # use in the generated row tuple. Note that some mappings include a string
    # substitution portion to accept sanitized versions of, for example, cookie
    # names, or HTTP header fields.
    FIELD_DEFS = {
        'a': ('remote_ip',         'address'),
        'A': ('local_ip',          'address'),
        'B': ('size',              'integer'),
        'b': ('size_clf',          'integer'),
        'C': ('cookie_%s',         'string'),
        'D': ('time_taken_ms',     'integer'),
        'e': ('env_%s',            'string'),
        'f': ('filename',          'path'),
        'h': ('remote_host',       'hostname'),
        'H': ('protocol',          'protocol'),
        'i': ('req_%s',            'string'),
        'k': ('keepalive',         'integer'),
        'l': ('ident',             'string'),
        'm': ('method',            'method'),
        'n': ('note_%s',           'string'),
        'o': ('resp_%s',           'string'),
        'p': ('port',              'integer'),
        'P': ('pid',               'integer'),
        'q': ('url_query',         'url'),
        'r': ('request',           'request'),
        'R': ('handler',           'string'),
        's': ('status',            'integer'),
        't': ('time',              'time'),
        'T': ('time_taken',        'integer'),
        'u': ('remote_user',       'string'),
        'U': ('url_stem',          'url'),
        'v': ('server_name',       'hostname'),
        'V': ('canonical_name',    'hostname'),
        'X': ('connection_status', 'keepalive'),
        'I': ('bytes_received',    'integer'),
        'O': ('bytes_sent',        'integer'),
        }

    TYPES = {
        'address':   (parsers.address_parse,  parsers.ADDRESS),
        'path':      (parsers.path_parse,     parsers.PATH),
        'hostname':  (parsers.hostname_parse, parsers.HOSTNAME),
        'integer':   (parsers.int_parse,      parsers.INTEGER),
        'method':    (None,                   parsers.METHOD),
        'protocol':  (None,                   parsers.PROTOCOL),
        'request':   (parsers.request_parse,  parsers.REQUEST),
        'url':       (parsers.url_parse,      parsers.URL),
        # Apache escapes non-printable and "special" chars with hex (\xhh)
        # sequences, except for newline, tab, and double-quote which are all
        # simply back-slash escaped. This is Apache specific and hence isn't
        # taken from the standard parsers module
        'string':    (string_parse,           r'(?P<%(name)s>([^\x00-\x1f\x7f\\"]|\\x[0-9a-fA-F]{2}|\\[^x])+|-)'),
        # Apache field type which indicates the keep-alive state of the
        # connection when the request is done (X=connection aborted before
        # completion, +=keep connection alive, -=close connection)
        'keepalive': (None,                   r'(?P<%(name)s>[X+-])'),
        # Apache can include just about anything at all in a time format string
        # so we special-case this type and construct a custom regex and parsing
        # function for it later from the format given
        'time':      (None,                   None),
        }

    def _parse_log_format(self):
        self._row_pattern = ''
        self._row_funcs = []
        self._row_type = None
        tuple_fields = []
        # re.split() returns (when given a pattern with a matching group) a
        # list composed of [str, sep, str, sep, str, ...]. However, our pattern
        # is actually intended to match format strings rather than separators
        # (which could be anything) so instead we'll get back something like
        # [sep, str, sep, str, sep, ...]. This is why separator is initially
        # True below
        separator = True
        for s in self.FIELD_RE1.split(self.log_format):
            if s:
                if separator:
                    self._row_pattern += re.escape(s)
                else:
                    name, pattern, parser = self._parse_log_field(s)
                    tuple_fields.append(name)
                    self._row_pattern += pattern
                    self._row_funcs.append(parser)
            separator = not separator
        self._row_type = dt.row(*tuple_fields)

    def _parse_log_field(self, s):
        # This function parses a single %{field}s in an Apache LogFormat
        # string; it is called by _parse_log_format which handles splitting up
        # the LogFormat into individual segments
        m = self.FIELD_RE2.match(s)
        if m:
            data, suffix = m.group('field'), m.group('suffix')
        else:
            # This should never happen
            raise RuntimeError('Internal error in FIELD_RE2')
        try:
            # General case: simple lookup to determine field name
            template, field_type = self.FIELD_DEFS[suffix]
        except KeyError:
            raise ValueError('Invalid format suffix "%s"' % suffix)
        name = self._generate_name(template, data, suffix)
        pattern, parser = self._generate_parser(data, field_type, field_name)
        return field_name, pattern, parser

    def _generate_name(self, template, data, suffix):
        # This function constructs the field name from the FIELD_DEFS template,
        # the field extracted from the spec (if any) and the type suffix. The
        # result MUST be a valid Python identifier
        if suffix in 'Ceino':
            # If a data is expected, sanitize it and substitute into template
            if not data:
                raise ValueError(
                    'Missing {str} for format suffix "%s"' % suffix)
            return template % dt.sanitize_name(data)
        elif suffix == 'p':
            # Special case: port
            if data:
                try:
                    return {
                        'canonical': 'port',
                        'local':     'local_port',
                        'remote':    'remote_port',
                        }[data]
                except KeyError:
                    raise ValueError('Invalid format in "%%{%s}p"' % data)
        elif suffix == 'P':
            # Special case: PID
            if data:
                try:
                    return {
                        'pid': 'pid',
                        'tid': 'tid',
                        'hextid': 'hextid',
                        }[data]
                except KeyError:
                    raise ValueError('Invalid format in "%%{%s}P"' % data)
        else:
            return template

    def _generate_parser(self, data, field_type, field_name):
        if field_type == 'time':
            # Special case: time. Use the Python's internal _strptime.TimeRE to
            # convert the strftime format into a locale-dependent unanchored
            # regex. For Python 2.7, a backport of Python 3.2's _strptime is
            # used as the former lacks support for the %z format spec.
            if data:
                fmt_locale = None
                fmt = data
            else:
                fmt_locale = EnglishLocalTime()
                fmt = APACHE_TIME
            try:
                time_regex = TimeRE(fmt_locale).pattern(fmt)
            except KeyError as exc:
                raise ValueError(
                    'Invalid time format spec %%%s in %s' % (str(exc), fmt))
            # Wrap the generated regex in a capturing pattern with a name
            # placeholder
            pattern = '(?P<%%(name)s>%s)' % time_regex
            # Derive a parser for parsing the particular time format
            parser = functools.partial(time_parse, fmt=fmt)
        else:
            parser, pattern = self.TYPES[field_type]
            if parser is None:
                parser = lambda s: s
        return pattern % {'name': field_name}, parser
