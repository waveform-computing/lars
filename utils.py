#!/usr/bin/env python
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

"""Installation utility functions"""

from __future__ import (
    unicode_literals,
    print_function,
    absolute_import,
    division,
    )

import io
import re

def get_version(filename):
    """
    Trivial parser to extract a __version__ variable from a source file.

    :param str filename: the file to extract __version__ from
    :returns str: the version string for the package
    """
    version_re = re.compile(r'(\d\.\d(\.\d+)?)')
    with io.open(filename, 'r') as source:
        for line_num, line in enumerate(source):
            if line.startswith('__version__'):
                match = version_re.search(line)
                if not match:
                    raise Exception(
                        'Invalid __version__ string found on '
                        'line %d of %s' % (line_num + 1, filename))
                return match.group(1)
    raise Exception('No __version__ line found in %s' % filename)

def description(filename):
    """
    Returns the first non-heading paragraph from a ReStructuredText file.

    :param str filename: the file to extract the description from
    :returns str: the description of the package
    """
    state = 'before_header'
    result = []
    # We use a simple DFA to parse the file which looks for blank, non-blank,
    # and heading-delimiter lines.
    with io.open(filename, 'r') as rst_file:
        for line in rst_file:
            line = line.rstrip()
            # Manipulate state based on line content
            if line == '':
                if state == 'in_para':
                    state = 'after_para'
            elif line == '=' * len(line):
                if state == 'before_header':
                    state = 'in_header'
                elif state == 'in_header':
                    state = 'before_para'
            else:
                if state == 'before_para':
                    state = 'in_para'
            # Carry out state actions
            if state == 'in_para':
                result.append(line)
            elif state == 'after_para':
                break
    return ' '.join(line.strip() for line in result)

