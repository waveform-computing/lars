.. _changelog:

==========
Change log
==========


Release 1.0 (2017-01-04)
========================

* Permit NULL values in first row when creating SQL tables (but warn as this is
  not encouraged)

* Permit sources and targets to be used outside of context handlers (makes
  experimentation in the REPL a bit nicer)

* Don't warn when request is NULL in Apache log sources (in certain
  configurations this is common when stringent timeouts are set)

* Fixed incorrect generation of Oracle multi-row INSERT statements

* Fixed operation of SQL target when row doesn't cover complete set of target
  table rows


Release 0.3 (2014-09-07)
========================

* Implemented Python 3 compatibility (specifically 3.2 or above) and added
  debian packaging for Python 3 and docs


Release 0.2 (2013-07-28)
========================

* Added ISP and organisation lookups to geoip module

* Added multi-row insertion support to the sql module

* Added Oracle specific target in the sql module

* Fixed the setup.py script (missing MANIFEST.in meant utils.py was excluded
  which setup.py relies upon)

* Fixed test coverage for the progress module


Release 0.1 (2013-06-09)
========================

* Initial release
