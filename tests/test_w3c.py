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

from www2csv import w3c
from nose.tools import assert_raises


def test_directive_regexes():
    assert w3c.W3CWrapper.VERSION_RE.match('#Version: 1.0')
    assert w3c.W3CWrapper.VERSION_RE.match('# VERSION : 1.0')
    assert w3c.W3CWrapper.VERSION_RE.match('# version:100.99')
    assert not w3c.W3CWrapper.VERSION_RE.match('#Version: foo')
    assert w3c.W3CWrapper.START_DATE_RE.match('#Start-Date: 2000-01-01 00:00:00')
    assert w3c.W3CWrapper.START_DATE_RE.match('# START-DATE : 2012-04-28 23:59:59')
    assert w3c.W3CWrapper.START_DATE_RE.match('# start-date:1976-01-01 09:00:00')
    assert not w3c.W3CWrapper.START_DATE_RE.match('#Start-Date: 2012-06-01')
    assert w3c.W3CWrapper.END_DATE_RE.match('#End-Date: 2000-01-01 00:00:00')
    assert w3c.W3CWrapper.END_DATE_RE.match('# END-DATE : 2012-04-28 23:59:59')
    assert w3c.W3CWrapper.END_DATE_RE.match('# end-date:1976-01-01 09:00:00')
    assert not w3c.W3CWrapper.END_DATE_RE.match('#End-Date: 2012-06-01')
    assert w3c.W3CWrapper.DATE_RE.match('#Date: 2000-01-01 00:00:00')
    assert w3c.W3CWrapper.DATE_RE.match('# DATE : 2012-04-28 23:59:59')
    assert w3c.W3CWrapper.DATE_RE.match('# date:1976-01-01 09:00:00')
    assert not w3c.W3CWrapper.DATE_RE.match('#Date: 2012-06-01')
    assert w3c.W3CWrapper.SOFTWARE_RE.match('#Software: foo')
    assert w3c.W3CWrapper.SOFTWARE_RE.match('# software : bar')
    assert w3c.W3CWrapper.REMARK_RE.match('#Remark: bar')
    assert w3c.W3CWrapper.REMARK_RE.match('# remark : bar')
    assert w3c.W3CWrapper.FIELDS_RE.match('#Fields: foo cs-foo rs(foo)')
    assert w3c.W3CWrapper.FIELDS_RE.match('# fields : x(bar) date time s-bar')
    assert w3c.W3CWrapper.FIELD_RE.match('foo')
    assert w3c.W3CWrapper.FIELD_RE.match('cs-foo')
    assert w3c.W3CWrapper.FIELD_RE.match('rs(foo)')
    assert w3c.W3CWrapper.FIELD_RE.match('x(bar)')
    # We can't deny invalid prefixes as the standard doesn't limit what
    # characters may appear in an identifier (and MS has already used the "-"
    # delimiter in several of their non-listed fields), so the best we can do
    # is match and make sure the prefix stays None
    assert w3c.W3CWrapper.FIELD_RE.match('foo(bar)').group('prefix') is None
    assert w3c.W3CWrapper.FIELD_RE.match('foo(bar)').group('identifier') == 'foo(bar)'

def test_sanitize_name():
    assert w3c.sanitize_name('foo') == 'foo'
    assert w3c.sanitize_name('FOO') == 'FOO'
    assert w3c.sanitize_name(' foo ') == '_foo_'
    assert w3c.sanitize_name('rs-date') == 'rs_date'
    assert w3c.sanitize_name('cs(User-Agent)') == 'cs_User_Agent_'
    assert_raises(ValueError, w3c.sanitize_name, '')

