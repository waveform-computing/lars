# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright (c) 2013 Python Software Foundation
# Portions (c) 2013-2017 Dave Jones
#
# PSF LICENSE AGREEMENT FOR PYTHON 3.2.3
#
# 1. This LICENSE AGREEMENT is between the Python Software Foundation
#    (“PSF”), and the Individual or Organization (“Licensee”) accessing
#    and otherwise using Python 3.2.3 software in source or binary form and its
#    associated documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF
#    hereby grants Licensee a nonexclusive, royalty-free, world-wide license
#    to reproduce, analyze, test, perform and/or display publicly, prepare
#    derivative works, distribute, and otherwise use Python 3.2.3 alone or in
#    any derivative version, provided, however, that PSF’s License Agreement
#    and PSF’s notice of copyright, i.e., “Copyright © 2001-2012 Python
#    Software Foundation; All Rights Reserved” are retained in Python 3.2.3
#    alone or in any derivative version prepared by Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on or
#    incorporates Python 3.2.3 or any part thereof, and wants to make the
#    derivative work available to others as provided herein, then Licensee
#    hereby agrees to include in any such work a brief summary of the changes
#    made to Python 3.2.3.
#
# 4. PSF is making Python 3.2.3 available to Licensee on an “AS IS” basis.
#    PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED. BY WAY OF
#    EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION
#    OR WARRANTY OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR
#    THAT THE USE OF PYTHON 3.2.3 WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON 3.2.3
#    FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT
#    OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 3.2.3, OR ANY
#    DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material breach
#    of its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any
#    relationship of agency, partnership, or joint venture between PSF and
#    Licensee. This License Agreement does not grant permission to use PSF
#    trademarks or trade name in a trademark sense to endorse or promote
#    products or services of Licensee, or any third party.
#
# 8. By copying, installing or otherwise using Python 3.2.3, Licensee agrees to
#    be bound by the terms and conditions of this License Agreement.

"""
This module is a backport of the Python 3.2 datetime.timezone class
implementation. End users should never need to refer to this module directly.
"""

# pylint: skip-file
# flake8: noqa

from datetime import tzinfo, timedelta, datetime

class timezone(tzinfo):
    __slots__ = '_offset', '_name'

    # Sentinel value to disallow None
    _Omitted = object()
    def __new__(cls, offset, name=_Omitted):
        if not isinstance(offset, timedelta):
            raise TypeError("offset must be a timedelta")
        if name is cls._Omitted:
            if not offset:
                return cls.utc
            name = None
        elif not isinstance(name, str):
            raise TypeError("name must be a string")
        if not cls._minoffset <= offset <= cls._maxoffset:
            raise ValueError("offset must be a timedelta"
                             " strictly between -timedelta(hours=24) and"
                             " timedelta(hours=24).")
        if (offset.microseconds != 0 or
            offset.seconds % 60 != 0):
            raise ValueError("offset must be a timedelta"
                             " representing a whole number of minutes")
        return cls._create(offset, name)

    @classmethod
    def _create(cls, offset, name=None):
        self = tzinfo.__new__(cls)
        self._offset = offset
        self._name = name
        return self

    def __getinitargs__(self):
        """pickle support"""
        if self._name is None:
            return (self._offset,)
        return (self._offset, self._name)

    def __eq__(self, other):
        return self._offset == other._offset

    def __hash__(self):
        return hash(self._offset)

    def __repr__(self):
        """Convert to formal string, for repr().

        >>> tz = timezone.utc
        >>> repr(tz)
        'datetime.timezone.utc'
        >>> tz = timezone(timedelta(hours=-5), 'EST')
        >>> repr(tz)
        "datetime.timezone(datetime.timedelta(-1, 68400), 'EST')"
        """
        if self is self.utc:
            return 'datetime.timezone.utc'
        if self._name is None:
            return "%s(%r)" % ('datetime.' + self.__class__.__name__,
                               self._offset)
        return "%s(%r, %r)" % ('datetime.' + self.__class__.__name__,
                               self._offset, self._name)

    def __str__(self):
        return self.tzname(None)

    def utcoffset(self, dt):
        if isinstance(dt, datetime) or dt is None:
            return self._offset
        raise TypeError("utcoffset() argument must be a datetime instance"
                        " or None")

    def tzname(self, dt):
        if isinstance(dt, datetime) or dt is None:
            if self._name is None:
                return self._name_from_offset(self._offset)
            return self._name
        raise TypeError("tzname() argument must be a datetime instance"
                        " or None")

    def dst(self, dt):
        if isinstance(dt, datetime) or dt is None:
            return None
        raise TypeError("dst() argument must be a datetime instance"
                        " or None")

    def fromutc(self, dt):
        if isinstance(dt, datetime):
            if dt.tzinfo is not self:
                raise ValueError("fromutc: dt.tzinfo "
                                 "is not self")
            return dt + self._offset
        raise TypeError("fromutc() argument must be a datetime instance"
                        " or None")

    _maxoffset = timedelta(hours=23, minutes=59)
    _minoffset = -_maxoffset

    @staticmethod
    def _name_from_offset(delta):
        if delta < timedelta(0):
            sign = '-'
            delta = -delta
        else:
            sign = '+'
        hours, rest = divmod(delta, timedelta(hours=1))
        minutes = rest // timedelta(minutes=1)
        return 'UTC{}{:02d}:{:02d}'.format(sign, hours, minutes)

timezone.utc = timezone._create(timedelta(0))
timezone.min = timezone._create(timezone._minoffset)
timezone.max = timezone._create(timezone._maxoffset)
