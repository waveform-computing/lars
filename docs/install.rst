.. _install:

=======
Install
=======

lars is distributed in several formats. The following sections detail
installation on a variety of platforms.


Pre-requisites
==============

Where possible, installation methods will automatically handle all mandatory
pre-requisites. However, if your particular installation method does not handle
dependency installation, then you will need to install the following Python
packages manually:

 * `pygeoip`_ - The pure Python API for MaxMind GeoIP databases

 * `ipaddress`_ - Google's IPv4 and IPv6 address handling library. This is
   included as standard in Python 3.3 and above.


Ubuntu Linux
============

For Ubuntu Linux, it is simplest to install from the `Waveform PPA`_ as follows
(this also ensures you are kept up to date as new releases are made):

.. code-block:: console

    $ sudo add-apt-repository ppa://waveform/ppa
    $ sudo apt-get update
    $ sudo apt-get install python-lars


Other Platforms
===============

If your platform is *not* covered by one of the sections above, lars is
available from PyPI and can therefore be installed with the Python setuptools
``easy_install`` tool:

.. code-block:: console

   $ easy_install lars

Or the (now deprecated) distribute ``pip`` tool:

.. code-block:: console

   $ pip install lars

If you do not have either of these tools available, please install the Python
`setuptools`_ package first.


.. _Waveform PPA: https://launchpad.net/~waveform/+archive/ppa
.. _pygeoip: https://pypi.python.org/pypi/pygeoip/
.. _ipaddress: https://pypi.python.org/pypi/ipaddress/
.. _setuptools: https://pypi.python.org/pypi/setuptools/
