# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

from .feature import _LinacFeature
from PyTango import Except as PyTangoExcept
from PyTango import ErrSeverity

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

ATTR='Attr'

class Formula(_LinacFeature):
    _read = None
    _readAttrs = None
    _write = None
    _writeAttrs = None
    _write_not_allowed = None

    def __init__(self, owner, read=None, write=None, write_not_allowed=None,
                 *args, **kwargs):
        super(Formula, self).__init__(owner=owner, *args, **kwargs)
        if read is not None:
            self._read = read
            self.info("configured read formula: %s" % (self._read))
            self._readAttrs = self._parse4Attr(self._read)
            self.info("found those attributes in the read formula: %s"
                      % (self._readAttrs))
        if write is not None:
            self._write = write
            self.info("configured write formula: %s" % (self._read))
            self._writeAttrs = self._parse4Attr(self._write)
            self.info("found those attributes in the write formula: %s"
                      % (self._readAttrs))
        self._write_not_allowed = write_not_allowed

    def __str__(self):
        _str_ = "%s {" % (self.name)
        for each in ['read', 'write', 'write_not_allowed']:
            value = self._getComponentValue(each)
            if value is not None:
                _str_ += "%s, " % (value)
        return _str_[:-2]+"}"

    @property
    def read(self):
        return self._read

    def readHook(self, value):
        formula = self._read
        modified = self._replaceAttrs4Values(formula, self._readAttrs)
        solution = self._solve(value, modified)
        self.debug("with VALUE=%s, %r means %s" % (value, formula, solution))
        return solution

    @property
    def readAttrs(self):
        if isinstance(self._readAttrs, dict):
            if len(self._readAttrs.keys()) > 0:
                return self._readAttrs

    @property
    def write(self):
        return self._write

    def writeHook(self, value):
        formula = self._write
        modified = self._replaceAttrs4Values(formula, self._writeAttrs)
        solution = self._solve(value, modified)
        self.debug("with VALUE=%s, %r means %s" % (value, formula, solution))
        if self.write_not_allowed is not None:
            if value != solution:
                PyTangoExcept.throw_exception("Write %s not allowed" % value,
                                              self.write_not_allowed,
                                              self.owner.name,
                                              ErrSeverity.WARN)
        return solution

    @property
    def writeAttrs(self):
        if isinstance(self._writeAttrs, dict):
            if len(self._writeAttrs.keys()) > 0:
                return self._writeAttrs

    @property
    def write_not_allowed(self):
        return self._write_not_allowed

    def _solve(self, VALUE, formula):
        result = eval(formula)
        self.debug("solve eval(\"%s\") = %s" % (formula, result))
        return result

    def _parse4Attr(self, formula):
        attrs = {}
        self.debug("parsing %r formula" % (formula))
        for pattern in formula.split(' '):
            self.debug("\tprocessing %r" % (pattern))
            if pattern.startswith(ATTR):
                self.debug("\t\tit starts with %s" % (ATTR))
                name = pattern.partition('[')[-1].rpartition(']')[0]
                self.debug("\t\tunderstood %s as attr name" % (name))
                method = pattern.split('.')[1]
                self.debug("\t\tunderstood %s as the method" % (method))
                # TODO: check that the attr name exist and the method
                #       will be callable to replace the given value
                #       in the formula
                # TODO: monitor! addReportTo(...) to reevalueate the formula
                #       if an attribute in here has change its value
                attrs[name] = pattern
        return attrs

    def _getAttrObj(self, name):
        try:
            return self.owner.device._getAttrStruct(name)
        except Exception as e:
            self.error("Cannot get the attrStruct for %s: %s" % (name, e))
            return None

    def _replaceAttrs4Values(self, formula, attrs):
        for name, pattern in self._readAttrs.iteritems():
            obj = self._getAttrObj(name)
            method = pattern.split('.')[1]
            if obj is not None and hasattr(obj, method):
                value = str(getattr(obj, method))
                new = formula.replace(pattern, value)
                formula = new
        return formula