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
Defines the URL parsing specific parts of :mod:`lars.datatypes`.
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from collections import namedtuple
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from .ipaddress import hostname

str = type('')  # pylint: disable=redefined-builtin,invalid-name


def path(s):
    """
    Returns a :class:`Path` object for the given string.

    :param str s: The string containing the path to parse
    :returns: A :class:`Path` object representing the path
    """
    i = s.rfind('/') + 1
    dirname, basename = s[:i], s[i:]
    if dirname and dirname != '/' * len(dirname):
        dirname = dirname.rstrip('/')
    i = basename.rfind('.')
    if i > 0:
        ext = basename[i:]
    else:
        ext = ''
    return Path(dirname, basename, ext)


def url(s):
    """
    Returns a :class:`Url` object for the given string.

    :param str s: The string containing the URL to parse
    :returns: A :class:`Url` tuple representing the URL
    """
    return Url(*parse.urlparse(s))


def request(s):
    """
    Returns a :class:`Request` object for the given string.

    :param str s: The string containing the request line to parse
    :returns: A :class:`Request` tuple representing the request line
    """
    try:
        method, s = s.split(' ', 1)
    except ValueError:
        raise ValueError('Request line is missing a space separated method')
    try:
        s, protocol = s.rsplit(' ', 1)
    except ValueError:
        raise ValueError('Request line is missing a space separated protocol')
    s = s.strip()
    if not s:
        raise ValueError('Request line URL cannot be blank')
    return Request(method, url(s) if s != '*' else None, protocol)


class Path(namedtuple('Path', 'dirname basename ext')):
    """
    Represents a path.

    This type is returned by the :func:`path` function and represents a path in
    POSIX format (forward slash separators and no drive portion). It is used to
    represent the path portion of URLs and provides attributes for extracting
    parts of the path there-in.

    The original path can be obtained as a string by asking for the string
    conversion of this class, like so::

        p = datatypes.path('/foo/bar/baz.ext')
        assert p.dirname == '/foo/bar'
        assert p.basename == 'baz.ext'
        assert str(p) == '/foo/bar/baz.ext'

    .. attribute:: dirname

       A string containing all of the path except the basename at the end

    .. attribute:: basename

       A string containing the basename (filename and extension) at the end
       of the path

    .. attribute:: ext

       A string containing the filename's extension (including the leading dot)
    """

    __slots__ = ()

    @property
    def dirs(self):
        """
        Returns a sequence of the directories making up :attr:`dirname`
        """
        return [d for d in self.dirname.split('/') if d]

    @property
    def basename_no_ext(self):
        """
        Returns a string containing basename with the extension removed
        (including the final dot separator).
        """
        if self.ext:
            return self.basename[:-len(self.ext)]
        else:
            return self.basename

    @property
    def isabs(self):
        """
        Returns True if the path is absolute (dirname begins with one or more
        forward slashes).
        """
        return self.dirname.startswith('/')

    def join(self, *paths):
        """
        Joins this path with the specified parts, returning a new :class:`Path`
        object.

        :param \\*paths: The parts to append to this path
        :returns: A new :class:`Path` object representing the extended path
        """
        # pylint: disable=invalid-name
        result = str(self)
        for p in paths:
            if not isinstance(p, str):
                p = str(p)
            # Strip doubled slashes? Or leave this to normpath?
            if p.startswith('/'):
                result = p
            elif not result or result.endswith('/'):
                result += p
            else:
                result += '/' + p
        return path(result)

    def __str__(self):
        result = self.dirname
        if not result or result.endswith('/'):
            return result + self.basename
        else:
            return result + '/' + self.basename


# This is rather hackish; in Python 2.x, urlparse.ResultMixin provides
# functionality for extracting username, password, hostname and port from a
# parsed URL. In Python 3 this changed to ResultBase, then to a whole bunch of
# undocumented classes (split between strings and bytes) with ResultBase as an
# alias
try:
    _ResultMixin = parse.ResultBase  # pylint: disable=invalid-name
except AttributeError:
    _ResultMixin = parse.ResultMixin  # pylint: disable=invalid-name


class Url(namedtuple('Url', ('scheme', 'netloc', 'path_str', 'params',
                             'query_str', 'fragment')), _ResultMixin):
    """
    Represents a URL.

    This type is returned by the :func:`url` function and represents the parts
    of the URL. You can obtain the original URL as a string by requesting the
    string conversion of this class, for example::

        >>> u = datatypes.url('http://foo/bar/baz')
        >>> print u.scheme
        http
        >>> print u.hostname
        foo
        >>> print str(u)
        http://foo/bar/baz

    .. attribute:: scheme

       The scheme of the URL, before the first ``:``

    .. attribute:: netloc

       The "network location" of the URL, comprising the hostname and port
       (separated by a colon), and historically the username and password
       (prefixed to the hostname and separated with an ampersand)

    .. attribute:: path_str

       The path of the URL from the first slash after the network location

    .. attribute:: path

       The path of the URL, parsed into a tuple which splits out the directory,
       filename, and extension::

          >>> u = datatypes.url('foo/bar/baz.html')
          >>> u.path
          Path(dirname='foo/bar', basename='baz.html', ext='.html')
          >>> u.path.isabs
          False

    .. attribute:: params

       The parameters of the URL

    .. attribute:: query_str

       The query string of the URL from the first question-mark in the path

    .. attribute:: query

       The query string, parsed into a mapping of keys to lists of values. For
       example::

          >>> u = datatypes.url('foo/bar?a=1&a=2&b=3&c=')
          >>> print u.query
          {'a': ['1', '2'], 'c': [''], 'b': ['3']}
          >>> print 'a' in u.query
          True

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
        """
        Return the URL as a string string.
        """
        return parse.urlunparse(self)

    def __str__(self):
        return self.geturl()

    @property
    def hostname(self):
        return hostname(super(Url, self).hostname)

    @property
    def query(self):
        # pylint: disable=missing-docstring
        return parse.parse_qs(self.query_str, keep_blank_values=True)

    @property
    def path(self):
        # pylint: disable=missing-docstring
        return path(self.path_str)


class Request(namedtuple('Request', 'method url protocol')):
    """
    Represents an HTTP request line.

    This type is returned by the :func:`request` function and represents the
    three parts of an HTTP request line: the method, the URL (optional, can be
    None in the case of methods like OPTIONS), and the protocol. The following
    attributes exist:

    .. attribute:: method

       The method of the request (typically GET, POST, or PUT but can
       technically be any valid HTTP token)

    .. attribute:: url

       The requested URL. May be an absolute URL, an absolute path, an
       authority token, or None in the case that the request line contained "*"
       for the URL.

    .. attribute:: protocol

       The HTTP protocol version requested. A string of the format 'HTTP/x.y'
       where x.y is the version number. At the time of writing only HTTP/1.0
       and HTTP/1.1 are defined.
    """

    def __str__(self):
        return '%s %s %s' % (self.method, self.url, self.protocol)
