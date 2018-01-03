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
A typical lars script opens some log source, typically a file, and uses the
source and target wrappers provided by lars to convert the log entries into
some other format (potentially filtering and/or modifying the entries along the
way). A trivial script to convert IIS W3C style log entries into a CSV file is
shown below::

    import io
    from lars import iis, csv

    with io.open('webserver.log', 'r') as infile, \\
             io.open('output.csv', 'wb') as outfile:
        with iis.IISSource(infile) as source, csv.CSVTarget(outfile) as target:
            for row in source:
                target.write(row)

Going through this section by section we can see the following:

#. The first couple of lines import the necessary modules that we'll need; the
   standard Python :mod:`io` module for opening files, and the :mod:`iis` and
   :mod:`csv` modules from lars for converting the data.

#. Using :func:`io.open` we open the input file (with mode ``'r'`` for reading)
   and the output file (with mode ``'wb'`` for creating a new file and writing
   (binary mode) to it)

#. We wrap ``infile`` (the input file) with :class:`~lars.iis.IISSource` to
   parse the input file, and ``outfile`` (the output file) with
   :class:`~lars.csv.CSVTarget` to format the output file.

#. Finally, we use a simple loop to iterate over the rows in the source file,
   and the :meth:`~lars.csv.CSVTarget.write` method to write them to the
   target.

This is the basic structure of most lars scripts. Most extra lines for
filtering and manipulating rows appear within the loop at the end of the file,
although sometimes extra module configuration lines are required at the top.


Filtering rows
==============

The row object declared in the loop has attributes named after the columns of
the source (with characters that cannot appear in Python identifiers replaced
with underscores). To see the structure of a row you can simply print one and
then terminate the loop::

    import io
    from lars import iis, csv

    with io.open('webserver.log', 'r') as infile, \\
            io.open('output.csv', 'wb') as outfile:
        with iis.IISSource(infile) as source, csv.CSVTarget(outfile) as target:
            for row in source:
                print(row)
                break

Given the following input file (long lines indented for readability)::

    #Software: Microsoft Internet Information Services 6.0
    #Version: 1.0
    #Date: 2002-05-24 20:18:01
    #Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem
        cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent)
        cs(Referrer)
    2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm -
        200 7930 248 31
        Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server)
        http://64.224.24.114/

This will produce this output on the command line::

    Row(date=Date(2002, 5, 24), time=Time(20, 18, 1),
        c_ip=IPv4Address(u'172.224.24.114'), cs_username=None,
        s_ip=IPv4Address(u'206.73.118.24'), s_port=80, cs_method=u'GET',
        cs_uri_stem=Url(scheme='', netloc='', path=u'/Default.htm', params='',
        query_str='', fragment=''), cs_uri_query=None, sc_status=200,
        sc_bytes=7930, cs_bytes=248, time_taken=31.0,
        cs_User_Agent=u'Mozilla/4.0 (compatible; MSIE 5.01; Windows 2000
        Server)', cs_Referrer=Url(scheme=u'http', netloc=u'64.224.24.114',
         path=u'/', params='', query_str='', fragment=''))

From this one can see that field names like ``c-ip`` have been converted into
``c_ip`` (``-`` is an illegal character in Python identifiers). Furthermore it
is apparent that instead of simple strings being extracted, the data has been
converted into a variety of appropriate datatypes
(:class:`~lars.datatypes.Date` for the ``date`` field,
:class:`~lars.datatypes.Url` for the ``cs-uri-stem`` field, and so on). This
significantly aids in filtering rows based upon sub-attributes of the extracted
data.

For example, to filter on the year of the date::

    if row.date.year == 2002:
        target.write(row)

Alternatively, you could filter on whether or not the client IP belongs in a
particular network::

    if row.c_ip in datatypes.network('172.0.0.0/8'):
        target.write(row)

Or use Python's `string methods`_ to filter on any string::

    if row.cs_User_Agent.startswith('Mozilla/'):
        target.write(row)

Or any combination of the above::

    if row.date.year == 2002 and 'MSIE' in row.cs_User_Agent:
        target.write(row)


Manipulating row content
========================

If you wish to modify the output structure,the simplest method is to declare
the row structure you want at the top of the file (using the
:func:`~lars.datatypes.row` function) and then construct rows with the new
structure in the loop (using the result of the function)::

    import io
    from lars import datatypes, iis, csv

    NewRow = datatypes.row('date', 'time', 'client', 'url')

    with io.open('webserver.log', 'r') as infile, \\
            io.open('output.csv', 'wb') as outfile:
        with iis.IISSource(infile) as source, csv.CSVTarget(outfile) as target:
            for row in source:
                new_row = NewRow(row.date, row.time, row.c_ip, row.cs_uri_stem)
                target.write(new_row)

There is no need to convert column data back to strings for output; all
datatypes produced by lars source adapters have built-in string conversions
which all target adapters know to use.

.. _io: http://docs.python.org/2/library/io.html
.. _string methods:
   http://docs.python.org/2/library/stdtypes.html#string-methods
"""
