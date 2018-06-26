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

from ctypes import *
import _ctypes
import socket
import time
import array
import sys
import struct
import select
from copy import copy
import traceback
import threading

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


REMOTE = '10.0.7.1'


class DaveException(Exception):
    pass


class Shutdown(Exception):
    pass


# ### Higher Level ###
class Datablock(object):

    dc = None

    def __init__(self, sock, read_size, write_size,
                 info, debug, warn, error, checkAddr):
        self.sock = sock
        self.read_size = read_size
        self.write_size = write_size
        self.write_start = read_size-write_size
        self.buf = array.array('B')
        self._bufferMutex = threading.Semaphore()
        self.info_stream = info
        self.debug_stream = debug
        self.warn_stream = warn
        self.error_stream = error
        self._checks = {}
        self._recv = ''
        self.readall()

    def isGoodBlock(self, reading):
        if len(reading) != self.read_size:
            self.debug_stream("checking block %d!=%d"
                              % (len(reading), self.read_size))
            return False
        return self.doChecks(reading)

    def isBlockInverted(self, reading):
        aux = self.invertBlock(reading)
        return self.isGoodBlock(aux)

    def invertBlock(self, reading):
        return reading[-self.read_size:] + reading[:self.write_size]

    def setChecker(self, addr, values):
        '''Set up a list of valid values for a given address, to be used to
           decide is a given block is valid or not.
        '''
        if isinstance(addr, int) and isinstance(values, list):
            self.debug_stream("Adding a checker for address %d with values %s"
                              % (addr, values))
            self._checks[addr] = values
            return True
        return False

    def getChecker(self, addr):
        if isinstance(addr, int) and addr in self._checks.keys():
            return self._checks[addr]
        return []

    def getCheckersAddresses(self):
        return self._checks.keys()

    def doChecks(self, block):
        for addr in self.getCheckersAddresses():
            values = self.getChecker(addr)
            # self.debug_stream("Checking addr %d for values %s (%s)"
            #                   % (addr, values, repr(block[addr])))
            if not block[addr] in values:
                self.warn_stream("Check fail for address %d (%s)"
                                 % (addr, repr(block[addr])))
                return False
        return True

    def readall(self):
        E = ()  # FIXME: what does it means?
        ready = ([], [], [])
        ctr = 0
        while not ready[0]:
            ready = select.select([self.sock.fileno()], E, E, 0)
            if not ready[0]:
                ctr += 1
                time.sleep(0.1)
                if ctr == 30:
                    self.error_stream("In readall(): not ready, select "
                                      "returns '%s'" % (str(ready)))
                    return False
            else:
                pass  # self.debug_stream("ready = %s" % (str(ready)))
        retries = 0

        self._recv = ''
        while len(self._recv) != self.read_size:  # while rem>0:
            select.select([self.sock.fileno()], E, E)
            self._recv = self.sock.recv(8192)
            self.debug_stream("> received %d bytes" % (len(self._recv)))
            if len(self._recv) == 0:
                retries += 1
                # if retries == 10:
                #     self.debug_stream("After a second of consecutive "
                #                       "retries, abort the readall()")
                #     return False
                self.debug_stream("Nothing received from the PLC (try %d)"
                                  % (retries))
                time.sleep(0.1)
            else:
                retries = 0
                if len(self._recv) > self.read_size:
                    # Cut the extra read data ---
                    # self.debug_stream(">> Cut the extra read data (%d)"
                    #                   % (len(self._recv)))
                    self._recv = self._recv[-self.read_size:]
                elif len(self._recv) in \
                        [self.read_size-self.write_size,  # received DB22
                         self.write_size]:  # received DB20
                    # When the reading match with only one DB from the plc,
                    # try another read where the pending data would be
                    self.debug_stream(">> Received 1 DB (%d)"
                                      % (len(self._recv)))
                    pendings = self.sock.recv(8192)
                    if len(pendings) > self.read_size:
                        # when the pendings are more than the waited DB,
                        # use it as input.
                        self.debug_stream(">>> pending provides new data (%d)"
                                          % (len(pendings)))
                        self._recv = pendings[-self.read_size:]
                    elif len(self._recv)+len(pendings) == self.read_size:
                        # distinguish from the two part which goes first
                        if len(pendings) == self.write_size:
                            self.debug_stream(">>> pending completes data (%d)"
                                              % (len(pendings)))
                            self._recv += pendings
                        else:
                            self.debug_stream(">>> put pending first")
                            self._recv = pendings + self._recv
                # once data has the correct size, check contents
                if self.isGoodBlock(self._recv):
                    # self.debug_stream("< Well done")
                    pass  # this is a good reading
                elif self.isBlockInverted(self._recv):
                    # try to invert the DBs
                    self.debug_stream("< received block is inverted")
                    self._recv = self.invertBlock(self._recv)
                else:
                    self.debug_stream("< discard data (%d)"
                                      % (len(self._recv)))
                    self._recv = ''
        self._bufferMutex.acquire()
        self.buf = array.array('B')
        self.buf.fromstring(self._recv)
        self._bufferMutex.release()
        return True

    def get(self, idx, T, size):
        # print 'get',idx, T, size
        a = array.array(T)
        # print('buf[%d:%d] = %s' % (idx, idx+size, self.buf[idx:idx+size]))
        self._bufferMutex.acquire()
        dat = copy(self.buf[idx:idx+size][::-1])
        self._bufferMutex.release()
        # print('got[%d:%d] = %s' % (idx, idx+size, dat))
        # dat.byteswap()
        a.fromstring(dat.tostring())
        # a.byteswap()
        a.reverse()
        # print('Buffer[%d] = %s' % (idx, a))
        try:
            return a[0]
        except:
            # print("get Exception a=%s"%(repr(a)))
            raise Exception('Impossible to get register %d' % (idx))

    def get2(self, idx, T):
        T = '>'+T
        n = sizeof(T)
        self._bufferMutex.acquire()
        addr = addressof(self.buf)+idx
        ait = (i for i in self.buf[idx:idx+n])
        self._bufferMutex.release()
        a = array.array('B', ait)
        # ugly way to do MSB to LSB swapping
        for i in range(n/2):
            a[i], a[n-i-1] = a[n-i-1], a[i]
        vp = c_void_p(a.buffer_info()[0])
        return cast(vp, POINTER(T)).contents.value

    # shortcut for common c_types
    def u16(self, idx):
        return self.get(idx, 'H', 2)

    def i16(self, idx):
        return self.get(idx, 'h', 2)

    def b(self, idx):
        return self.get(idx, 'B', 1)

    def bit(self, idx, bitno):
        idx += bitno/8
        bitno %= 8
        v = self.b(idx)
        r = bool((v >> bitno) & 1)
        return r

    def f(self, idx):
        return self.get(idx, 'f', 4)

    def write(self, idx, f, T=None, dry=False):
        type_code, size = T[:2]
        self.debug_stream('write register %d (type %s,%s;) size %d bytes'
                          % (idx, f, type_code, size))
        a = self.write_start+idx
        z = a+size
        bar = struct.pack('>'+type_code, f)
        bytes = array.array('B', bar)
        # print a,z, bytes
        self.debug_stream('read in [%d:%d] (%d=%d+%d): %s'
                          % (a, z, a, self.write_start, idx, bytes))
        self._bufferMutex.acquire()
        self.buf[a:z] = bytes
        self._bufferMutex.release()
        if not dry:
            self.rewrite()

    def rewrite(self):
        self._bufferMutex.acquire()
        write_buf = self.buf[self.write_start:]
        self._bufferMutex.release()
        write_str = write_buf.tostring()
        try:
            assert (len(write_str) == self.write_size),\
                'len(write_str) %d != Write Size %d'\
                % (len(write_str), self.write_size)
        except Exception as e:
            msg = 'Write not possible: %s' % (e)
            self.error_stream(msg)
            raise Exception(msg)
        else:
            for x, ch in enumerate(write_str):
                o = ord(ch)
                # print "%3d: %2x (%d decimal)" % (x,o,o)
            self.sock.sendall(write_str)
            self.debug_stream("rewrite send: %s" % (repr(write_str)))


# reuse existing connections if possible
CONN = {
}


def open_datablock(hostname, port, read_size, write_size, REMOTE='0.0.0.0',
                   info=None, debug=None, warn=None, error=None,
                   checkAddr=None):
    '''Creates a Datablock for communicating with host 'host' on databloc
       dbnum which has size 'size'.
    '''
    if info:
        info("open_datablock(hostname:'%s',port:%d,read_size:%d,write_size:"
             "%d,REMOTE:'%s')" % (hostname, port, read_size, write_size,
                                  REMOTE))
    import os
    hostname = hostname.lower()
    conn = CONN.get(hostname)
    if conn is None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((REMOTE, port))
            sock.connect((hostname, port))
        except Exception as e:
            if error:
                error("open_datablock() exception: %s" % (e))
            raise e
    db = Datablock(sock, read_size, write_size, info, debug, warn, error,
                   checkAddr)
    return db


def close_datablock(db, warn=None):
    sock = db.sock
    db.sock = None
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except Exception as exc:
        if warn:
            warn(exc)
    try:
        sock.close()
    except Exception as exc:
        if warn:
            warn(exc)


if __name__ == '__main__':
        main()
