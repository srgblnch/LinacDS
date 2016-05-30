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
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


from ctypes import *
import _ctypes
import socket
import time
import array
import sys
import struct


class DaveException(Exception):
    pass

try:
    lib = CDLL('./libnodave.so64')
except OSError, exc:
    lib = CDLL('./libnodave.so32')

libc = CDLL('libc.so.6')
lib.daveNewInterface.restype = c_void_p
lib.daveNewConnection.restype = c_void_p

HANDLE = c_int
PROTO_ISOTCP = c_int(122)  # < ISO over TCP
SPEED_187k = c_int(2)
PORT_ISOTCP = 102

DAVE_P = c_int(0x80)
DAVE_INPUTS = c_int(0x81)
DAVE_OUTPUTS = c_int(0x82)
DAVE_FLAGS = c_int(0x83)
DAVE_DB = c_int(0x84)  # < data blocks
DAVE_DI = c_int(0x85)  # < instance data blocks
DAVE_LOCAL = c_int(0x86)  # < not tested
DAVE_V = c_int(0x87)  # < don't know what it is

DAVE_COUNTER = c_int(28)  # < S7 counters
DAVE_TIMER = c_int(29)  # < S7 timers
DAVE_COUNTER200 = c_int(30)  # < IEC counters (200 family)
DAVE_TIMER200 = c_int(31)

CType = c_int.__base__


class OSserialType(Structure):
    '''Directly maps daveOSserialType structure.
    '''
    _fields_ = (('rfd', HANDLE),
                ('wfd', HANDLE))


class Interface(object):
    '''Simplified dave interface object.
    '''
    ptr = None
    nname = c_char_p('IF1')
    localMPI = c_int(0)
    protocol = PROTO_ISOTCP
    speed = SPEED_187k

    def __init__(self, sock):
        '''maps to daveNewInterface
        '''
        fds = self.fds = OSserialType()
        self.fds.__sock = sock
        fds.wfd = fds.rfd = c_int(sock.fileno())
        self.ptr = lib.daveNewInterface(fds, self.nname, self.localMPI,
                                        self.protocol, self.speed)
        if not self.ptr:
            raise DaveException('could not allocate dave new interface')

    def __del__(self):
        print 'delete interface'
        sys.stdout.flush()

        if self.ptr and libc:
            libc.free(self.ptr)
            del self.ptr


class Connection(object):
    _fields_ = ()
    ptr = None

    def __init__(self, di):
        # stores a reference to di object to ensure that the connection is
        # collected before the interface is collected
        self.interface = di
        mpi = c_int(2)
        rack = c_int(0)
        slot = c_int(2)
        self.ptr = lib.daveNewConnection(di.ptr, mpi, rack, slot)
        if not self.ptr:
            raise DaveException('could not create new Connection')

    def __del__(self):
        sys.stdout.flush()

        if self.ptr and libc:
            p = self.ptr
            lib.daveDisconnectPLC(p)
            libc.free(self.ptr)
            del self.ptr

    def connect(self):
        res = lib.daveConnectPLC(self.ptr)
        if res != 0:
            raise DaveException('could not connect')

    def read_bytes(self, what, dbnum, offset, nwords, buf=None):
        if buf is None:
            nbytes = nwords
            buf = array.array('B', [0]*nbytes)

        if isinstance(buf, array.array):
            vp = c_void_p(buf.buffer_info()[0])
        else:
            vp = pointer(buf)

        res = lib.daveReadBytes(self.ptr, what, c_int(dbnum), c_int(offset),
                                c_int(nwords), vp)
        if res:
            msg = 'reading %d words from DB %d at offset %d failed (%s)'\
                  % (nwords, dbnum, offset, res)
            raise DaveException(msg)
        return buf

    def write_bytes(self, what, dbnum, offset, nwords, buf):
        if isinstance(buf, array.array):
            buf = c_void_p(buf.buffer_info()[0])
        res = lib.daveWriteBytes(self.ptr, what, c_int(dbnum), c_int(offset),
                                 c_int(nwords), buf)
        if res:
            msg = 'writing %d words into DB %d at offset %d failed (%s)'\
                  % (nwords, dbnum, offset, res)
            raise DaveException(msg)


# ### higher level ###
class Datablock(object):

    dc = None

    def __init__(self, dc, dbnum, nbytes, offset=0, what=DAVE_DB):
        self.dc = dc
        self.what = what
        self.dbnum = dbnum
        self.nbytes = nbytes
        self.offset = offset
        self.buf = (c_uint8 * (2*nbytes))()
        self.readall()

    def readall(self):
        self.dc.read_bytes(self.what, self.dbnum, self.offset, self.nbytes,
                           self.buf)

    def get(self, idx, T):
        n = sizeof(T)
        addr = addressof(self.buf)+idx
        ait = (i for i in self.buf[idx:idx+n])
        a = array.array('B', ait)
        # ugly way to do MSB to LSB swapping
        for i in range(n/2):
            a[i], a[n-i-1] = a[n-i-1], a[i]

        vp = c_void_p(a.buffer_info()[0])
        return cast(vp, POINTER(T)).contents.value

    def get2(self, idx, T):
        T = '>'+T
        n = sizeof(T)
        addr = addressof(self.buf)+idx
        ait = (i for i in self.buf[idx:idx+n])
        a = array.array('B', ait)
        # ugly way to do MSB to LSB swapping
        for i in range(n/2):
            a[i], a[n-i-1] = a[n-i-1], a[i]

        vp = c_void_p(a.buffer_info()[0])
        return cast(vp, POINTER(T)).contents.value

    # shortcut for common c_types
    def u16(self, idx):
        return self.get(idx, c_uint16)

    def i16(self, idx):
        return self.get(idx, c_int16)

    def b(self, idx):
        return self.get(idx, c_uint8)

    def bit(self, idx, bitno):
        v = self.get(idx, c_uint8)
        r = bool((v >> bitno) & 1)
        return r

    def f(self, idx):
        return self.get(idx, c_float)

    def write(self, idx, f, T=None):
        if T:
            f = T(f)
        else:
            T = f.__class__

        size = max(sizeof(T), 1)
        off = self.offset+idx
        addr = addressof(f)
        for i in range(size/2):
            a = cast(addr+i, POINTER(c_byte)).contents
            b = cast(addr+size-i-1, POINTER(c_byte)).contents
            a.value, b.value = b.value, a.value
        vp = c_void_p(addressof(f))
        self.dc.write_bytes(self.what, self.dbnum, off, size, byref(f))

# reuse existing connections if possible
CONN = {
}


def open_isotcp_datablock(hostname, dbnum, nwords, offset=0, what=DAVE_DB):
    '''Creates a Datablock for communicating with host 'host' on databloc
       dbnum which has size 'size'.
    '''
    hostname = hostname.lower()
    conn = CONN.get(hostname)
    if conn is None:
        sock = socket.socket()
        sock.connect((hostname, PORT_ISOTCP))
        ifc = Interface(sock)
        conn = Connection(ifc)
        conn.connect()
        CONN[hostname] = conn
    db = Datablock(conn, dbnum, nwords)
    return db


SCM_STAT = ('undef', 'moving', 'up', 'down', 'fault')


def write_bit(set_db, idx, bitno, v=1):
    v = bool(v)
    b = set_db.b(idx)
    b = b & ~(1 << bitno) | (v << bitno)
    set_db.write(idx, c_byte(b))

DOWN = True
UP = False


def scm_dc(x):
    return 'down' if x else 'up'


def main():
    import random
    name = '10.0.7.101'
#    name = '192.168.0.13'
    set_dbnum = 20  # local control block
    read_dbnum = 22  # TCP monitors
    nbytes = 166
    read_db = open_isotcp_datablock(name, read_dbnum, nbytes)
    set_db = open_isotcp_datablock(name, set_dbnum, 82)
    scm = 1
    COMM_ST_IDX = 82
    s = read_db.i16(160)
    print('status', s)
    print('status', read_db.i16(COMM_ST_IDX))

    if len(sys.argv) > 1:
        r = int(sys.argv[1])

    write_bit(set_db, 80, 0, 1)  # (un)lock
    read_db.readall()
    set_db.readall()
    set_db.write(76, c_int16(r))  # scm up/down

#    assert s==r

if __name__ == '__main__':
    main()
