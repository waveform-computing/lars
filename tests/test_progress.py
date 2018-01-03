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

import io
import pytest
import mock

from lars import progress

def test_spinner():
    style = progress.SpinnerStyle(None)
    # Grab the output of the spinner
    output = style.render(0, 0)
    for i in range(10):
        output += style.render(0, 0)
        if output[-1] == output[0]:
            break
    output = output[:-1]
    # Rotate the output string until it matches the expected one
    for i in range(len(output)):
        if output[i:] + output[:i] == '-\\|/':
            return
    assert False, "Spinner didn't output spinning line"

def test_ellipsis():
    style = progress.EllipsisStyle(None)
    style.max = 4
    # Grab the output of the ellipsis style
    output = []
    for i in range(style.max):
        output.append(style.render(0, 0))
    # Rotate the output until it matches the expected one
    for i in range(len(output)):
        if output[i:] + output[:i] == ['', '.', '..', '...']:
            return
    assert False, "Ellipsis didn't output incrementing pattern"

def test_percentage():
    style = progress.PercentageStyle(None)
    assert style.render(0, 10)  == '  0%'
    assert style.render(1, 10)  == ' 10%'
    assert style.render(2, 10)  == ' 20%'
    assert style.render(3, 10)  == ' 30%'
    assert style.render(4, 10)  == ' 40%'
    assert style.render(5, 10)  == ' 50%'
    assert style.render(6, 10)  == ' 60%'
    assert style.render(7, 10)  == ' 70%'
    assert style.render(8, 10)  == ' 80%'
    assert style.render(9, 10)  == ' 90%'
    assert style.render(10, 10) == '100%'

def test_bar():
    style = progress.BarStyle(None)
    style.width = 18
    style.fill_char = '='
    style.back_char = ' '
    assert len(style.render(0, 10)) == style.width
    assert style.render(0, 10)  == '[>          ]   0%'
    assert style.render(1, 10)  == '[=>         ]  10%'
    assert style.render(2, 10)  == '[==>        ]  20%'
    assert style.render(3, 10)  == '[===>       ]  30%'
    assert style.render(4, 10)  == '[====>      ]  40%'
    assert style.render(5, 10)  == '[=====>     ]  50%'
    assert style.render(6, 10)  == '[======>    ]  60%'
    assert style.render(7, 10)  == '[=======>   ]  70%'
    assert style.render(8, 10)  == '[========>  ]  80%'
    assert style.render(9, 10)  == '[=========> ]  90%'
    assert style.render(10, 10) == '[==========>] 100%'

def test_hash():
    style = progress.HashStyle(None)
    for i in range(1, 10):
        assert style.render(0, 0) == style.char * i

def test_meter_bad_init():
    with pytest.raises(ValueError):
        progress.ProgressMeter()
    with pytest.raises(ValueError):
        progress.ProgressMeter(fileobj=mock.Mock(), total=100)

def test_meter_time():
    with mock.patch('tests.test_progress.progress.time.time') as mock_time:
        mock_file = mock.Mock()
        mock_file.tell.return_value = 0
        mock_file.seek.return_value = 100
        stream = io.StringIO()
        mock_time.return_value = 0
        with progress.ProgressMeter(
                mock_file, stream=stream, max_wait=0.5,
                style=progress.PercentageStyle) as meter:
            s = '  0%'
            assert stream.getvalue() == s
            # Ensure if the time elapsed is less than max_wait, nothing happens
            mock_time.return_value = 0.2
            meter.update()
            assert stream.getvalue() == s
            # Ensure if the time elapsed is more than max_wait, but the value
            # hasn't changed the nothing still happens
            mock_time.return_value = 1.0
            meter.update()
            assert stream.getvalue() == s
            # Ensure that if the value has also changed, something happens
            mock_time.return_value = 2.0
            mock_file.tell.return_value = 10
            meter.update()
            s += ('\b' * 4) + (' ' * 4) + ('\b' * 4) + ' 10%'
            assert stream.getvalue() == s
            # Hide the meter and make sure nothing is displayed
            meter.hide()
            s += ('\b' * 4) + (' ' * 4) + ('\b' * 4)
            assert stream.getvalue() == s
        # Ensure that if it was already hidden, nothing gets done on context
        # exit
        assert stream.getvalue() == s

def test_meter_wait():
    with mock.patch('tests.test_progress.progress.time.time') as mock_time:
        stream = io.StringIO()
        mock_time.return_value = 0
        with progress.ProgressMeter(
                value=0, total=10, stream=stream, max_wait=0.5,
                style=progress.PercentageStyle, hide_on_finish=False) as meter:
            s = '  0%'
            assert stream.getvalue() == s
            mock_time.return_value = 1.0
            meter.update(1)
            s += ('\b' * 4) + (' ' * 4) + ('\b' * 4) + ' 10%'
            assert stream.getvalue() == s
            # Ensure that if the value changes, but time advance is not yet
            # max_wait, nothing happens
            meter.update(2)
            assert stream.getvalue() == s
        s += ('\b' * 4) + (' ' * 4) + ('\b' * 4) + ' 20%\n'
        assert stream.getvalue() == s
