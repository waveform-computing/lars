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
This is the root module for the www2csv package.

A typical www2csv script opens some log source, typically a file, and uses the
source and target wrappers provided by www2csv to convert the log entries into
some other format (potentially filtering and/or modifying the entries along the
way). A trivial script to convert IIS W3C style log entries into a CSV file is
shown below::

    import io
    from www2csv import w3c, csv

    with io.open('webserver.log', 'r') as infile, io.open('output.csv', 'w') as outfile:
        with w3c.W3CSource(infile) as source, csv.CSVTarget(outfile) as target:
            for row in source:
                target.write(row)

Going through this section by section we can see the following:

#. The first couple of lines import the necessary modules that we'll need; the
   standard Python `io`_ module for opening files, and the :mod:`w3c` and
   :mod:`csv` modules from www2csv for converting the data.

#. Using ``io.open`` we open the input file (with mode ``'r'`` for reading) and
   the output file (with mode ``'w'`` for creating a new file and writing to
   it)

#. We wrap ``infile`` (the input file) with :class:`~www2csv.w3c.W3CSource` to
   parse the input file, and ``outfile`` (the output file) with
   :class:`~www2csv.csv.CSVTarget` to format the output file.

#. Finally, we use a simple loop to iterate over the rows in the source file,
   and the :meth:`~www2csv.csv.CSVTarget.write` method to write them to the
   target.

This is the basic structure of most www2csv scripts. Most extra lines for
filtering and manipulating rows appear within the loop at the end of the file,
although sometimes extra module configuration lines are required at the top.


Filtering rows
==============

The row object declared in the loop has attributes named after the columns of
the source (with characters that cannot appear in Python identifiers replaced
with underscores). To see the structure of a row you can simply print one and
then terminate the loop::

    import io
    from www2csv import w3c, csv

    with io.open('webserver.log', 'r') as infile, io.open('output.csv', 'w') as outfile:
        with w3c.W3CSource(infile) as source, csv.CSVTarget(outfile) as target:
            for row in source:
                print(row)
                break

Given the following input file::

    #Software: Microsoft Internet Information Services 6.0
    #Version: 1.0
    #Date: 2002-05-24 20:18:01
    #Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
    2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/

This will produce this output on the command line::

    row_type(date=datetime.date(2002, 5, 24), time=datetime.time(20, 18, 1), c_ip=IPv4Address(u'172.224.24.114'), cs_username=None, s_ip=IPv4Address(u'206.73.118.24'), s_port=80, cs_method=u'GET', cs_uri_stem=Url(scheme='', netloc='', path='/Default.htm', params='', query='', fragment=''), cs_uri_query=None, sc_status=200, sc_bytes=7930, cs_bytes=248, time_taken=31.0, cs_User_Agent='Mozilla/4.0 (compatible; MSIE 5.01; Windows 2000 Server)', cs_Referrer='http://64.224.24.114/')

From this you can see that field names like ``c-ip`` have been converted into
``c_ip`` (as ``-`` is an illegal character in Python identifiers). You can
also see that instead of simple strings being extracted, the data has been
converted into a variety of appropriate datatypes (`datetime.date`_ for the
``date`` field, :class:`~www2csv.datatypes.Url` for the ``cs-uri-stem`` field,
and so on). This makes it trivial to filter based upon just about any element
of the extracted data.

For example, to filter on the year of the date::

    if row.date.year == 2002:
        target.write(row)

Alternatively, you could filter on whether or not the client IP belongs in a
particular network::

    if row.c_ip in datatypes.network('172.0.0.0/8'):
        target.write(row)

Or use Python's string methods to filter on any string::

    if row.cs_User_Agent.startswith('Mozilla/'):
        target.write(row)

Or any combination of the above::

    if row.date.year == 2002 and 'MSIE' in row.cs_User_Agent:
        target.write(row)


Manipulating row content
========================

If you wish to modify the output structure,the simplest method is to declare
the row structure you want at the top of the file (using the
:func:`~www2csv.datatypes.Row` function) and then construct rows with the new
structure in the loop (using the result of the function)::

    import io
    from www2csv import datatypes, w3c, csv

    NewRow = datatypes.Row('date', 'time', 'client', 'url')

    with io.open('webserver.log', 'r') as infile, io.open('output.csv', 'w') as outfile:
        with w3c.W3CSource(infile) as source, csv.CSVTarget(outfile) as target:
            for row in source:
                new_row = NewRow(row.date, row.time, row.c_ip, r.cs_uri_stem)
                target.write(new_row)

There is no need to convert column data to strings for output; all datatypes
produced by www2csv source adapters have built-in string conversions which all
target adapters know to use.

.. _io: http://docs.python.org/2/library/io.html
.. _datetime.date: http://docs.python.org/2/library/datetime.html#date
"""

__version__ = '0.1'
