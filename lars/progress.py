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
This module provides a wrapper that outputs simple progress meters to the
command line based on source file positions, or an arbitrary counter. The
:class:`ProgressMeter` class is the major element that this module provides.


Classes
=======

.. autoclass:: ProgressMeter(fileobj=None, value=0, total=None, max_wait=0.1, \
        stream=sys.stderr, mode='w', style=BarStyle, hide_on_finish=True)
   :members:

.. autoclass:: SpinnerStyle

.. autoclass:: PercentageStyle

.. autoclass:: EllipsisStyle

.. autoclass:: BarStyle

.. autoclass:: HashStyle


Examples
========

The most basic usage of this class is as follows::

    import io
    from lars import iis, csv, progress

    with io.open('logs\\iis.txt', 'rb') as infile, \\
            io.open('iis.csv', 'wb') as outfile, \\
            progress.ProgressMeter(infile) as meter, \\
            iis.IISSource(infile) as source, \\
            csv.CSVTarget(outfile) as target:
        for row in source:
            target.write(row)
            meter.update()

Note that you do not need to worry about the detrimental performance effects of
calling :meth:`~ProgressMeter.update` too often; the class ensures that
repeated calls are ignored until :attr:`~ProgressMeter.max_wait` seconds have
elapsed since the last update.

Alternatively, if you wish to update according to, say, the number of files to
process you could use something like the following example (which also
demonstrates temporarily hiding the progress meter in order to show the current
filename)::

    import os
    import io
    from lars import iis, csv, progress
    from pathlib import Path

    files = list(Path('.').iterdir())
    with progress.ProgressMeter(total=len(files),
                                style=progress.BarStyle) as meter:
        for file_num, file_name in enumerate(files):
            meter.hide()
            print "Processing %s" % file_name
            meter.show()
            with file_name.open('rb') as infile, \\
                    file_name.with_suffix('.csv').open('wb') as outfile, \\
                    iis.IISSource(infile) as source, \\
                    csv.CSVTarget(outfile) as target:
                for row in source:
                    target.write(row)
            meter.update(file_num)
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )


import io
import sys
import time

str = type('')  # pylint: disable=redefined-builtin,invalid-name


class ProgressStyle(object):
    """
    Abstract base class for :class:`ProgressMeter` styles.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, meter):
        """
        Perform initialization for the style, and set hide_on_finish
        """
        pass

    def render(self, value, total):
        """
        Return a string showing value/total progress
        """
        raise NotImplementedError


class SpinnerStyle(ProgressStyle):
    """
    A :class:`ProgressMeter` style that renders a simple spinning line.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, meter):
        super(SpinnerStyle, self).__init__(meter)
        self.index = 0

    def render(self, value, total):
        self.index += 1
        return ['/', '-', '\\', '|'][self.index % 4]


class EllipsisStyle(ProgressStyle):
    """
    A :class:`ProgressMeter` style that renders an looping series of dots.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, meter):
        super(EllipsisStyle, self).__init__(meter)
        self.count = 0
        self.max = 8

    def render(self, value, total):
        self.count += 1
        self.count %= self.max
        return '.' * self.count


class PercentageStyle(ProgressStyle):
    """
    A :class:`ProgressMeter` style that renders a simple percentage counter.
    """
    # pylint: disable=too-few-public-methods

    def render(self, value, total):
        return '%3d%%' % (100 * value // total)


class BarStyle(ProgressStyle):
    """
    A :class:`ProgressMeter` style that renders a full progress bar and
    percentage.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, meter):
        super(BarStyle, self).__init__(meter)
        self.width = 60
        self.fill_char = '='
        self.back_char = ' '

    def render(self, value, total):
        x = (self.width - 8) * value // total
        return '[%s>%s] %3d%%' % (
            self.fill_char * x,
            self.back_char * (self.width - 8 - x),
            100 * value // total,
            )


class HashStyle(ProgressStyle):
    """
    A :class:`ProgressMeter` style for those that remember FTP's ``hash``
    command!
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, meter):
        super(HashStyle, self).__init__(meter)
        self.count = 0
        self.char = '#'

    def render(self, value, total):
        self.count += 1
        return self.char * self.count


class ProgressMeter(object):
    """
    This class provides a simple means of rendering a progress meter at the
    command line. It can be driven either with a file object (in which case the
    current position of the file is used) or with an arbitrary value (which
    your code must provide). In the case of a file-object, the file must be
    seekable (so that the class can determine the overall length of the file).
    If *fileobj* is not specified, then *total* must be specified.

    The class is intended to be used as a context manager. Upon entry it will
    render an initial progress meter, and will update it at reasonable
    intervals (dictated by the max_wait parameter) in response to calls to the
    :meth:`update` method. When you leave the context, the progress meter will
    be automatically erased if *hide_on_finish* is True (which it is by
    default).

    Within the context, the :meth:`hide` and :meth:`show` methods can be used
    to temporarily hide and show the progress meter (in order to display some
    status text, for example).

    :param file fileobj:
        A file-like object from which to determine progress

    :param int value:
        An arbitrary value from which to determine progress

    :param int total:
        In the case that *value* is set, this must be set to the maximum value
        that *value* will take

    :param float max_wait:
        The minimum length of time that must elapse before a screen update is
        permitted

    :param file stream:
        The stream object that output should be written to, defaults to stderr

    :param style:
        A reference to a class which will be used to render the progress meter,
        defaults to :class:`BarStyle`

    :param bool hide_on_finish:
        If True (the default), the progress meter will be erased when the
        context exits
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(
            self, fileobj=None, value=0, total=None, max_wait=0.1,
            stream=sys.stderr, style=BarStyle, hide_on_finish=True):
        # pylint: disable=too-many-arguments
        if fileobj is None and total is None:
            raise ValueError('One of fileobj or total must be specified')
        if fileobj is not None and total is not None:
            raise ValueError('Only one of fileobj or total can be specified')
        self.max_wait = max_wait
        self.stream = stream
        self.hide_on_finish = hide_on_finish
        self.fileobj = fileobj
        if fileobj is None:
            self.value = value
            self.total = total
        else:
            self.value = self.fileobj.tell()
            try:
                self.total = self.fileobj.seek(0, io.SEEK_END)
            finally:
                self.fileobj.seek(self.value, io.SEEK_SET)
        self.style = style(self)
        self._last_value = self.value
        self._last_output = ''
        self._last_update = None

    def hide(self):
        """
        Hide the progress bar from the console (or whatever the output stream
        is connected to).
        """
        if self._last_output:
            self.stream.write('\b' * len(self._last_output))
            self.stream.write(' ' * len(self._last_output))
            self.stream.write('\b' * len(self._last_output))
            self.stream.flush()
            self._last_output = ''
        self._last_update = None

    def show(self):
        """
        Show the progress bar on the console (or whatever the output stream
        is connected to).
        """
        self._render()
        self._last_update = time.time()

    def update(self, value=None):
        """
        Update the progress bar to position *value* (which must be less than
        the *total* value passed to the constructor).
        """
        if value is None:
            value = self.fileobj.tell()
        self.value = value
        if value != self._last_value:
            now = time.time()
            if self._last_update is None or now > (self._last_update +
                                                   self.max_wait):
                self.hide()
                self._last_value = value
                self._render()
                self._last_update = now

    def _render(self):
        self._last_output = self.style.render(self._last_value, self.total)
        self.stream.write(self._last_output)
        self.stream.flush()

    def __enter__(self):
        self.show()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.hide()
        if not self.hide_on_finish:
            self._last_value = self.value
            self._render()
            self.stream.write('\n')
