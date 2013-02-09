# Written by John Hoffman
# see LICENSE.txt for license information

import socket
from bisect import bisect, insort

def to_long_ipv4(ip):
    shiftbyte = lambda x, y: 256*x + y
    return reduce(shiftbyte, map(ord, socket.inet_aton(ip)))

def to_long_ipv6(ip):
    if ip == '':
        raise ValueError, "bad address"
    if ip == '::':      # boundary handling
        ip = ''
    elif ip[:2] == '::':
        ip = ip[1:]
    elif ip[0] == ':':
        raise ValueError, "bad address"
    elif ip[-2:] == '::':
        ip = ip[:-1]
    elif ip[-1] == ':':
        raise ValueError, "bad address"

    b = []
    doublecolon = False
    for n in ip.split(':'):
        if n == '':     # double-colon
            if doublecolon:
                raise ValueError, "bad address"
            doublecolon = True
            b.append(None)
            continue
        if n.find('.') >= 0: # IPv4
            n = n.split('.')
            if len(n) != 4:
                raise ValueError, "bad address"
            b.extend(map(int,n))
            continue
        n = ('0'*(4-len(n))) + n
        b.append(int(n[:2],16))
        b.append(int(n[2:],16))
    bb = 0L
    for n in b:
        if n is None:
            for i in xrange(17-len(b)):
                bb *= 256
            continue
        bb *= 256
        bb += n
    return bb

ipv4addrmask = 65535L*256*256*256*256

class IP_List:
    def __init__(self, entrylist=None):
        self.ipv4list = []  # starts of ranges
        self.ipv4dict = {}  # start: end of ranges
        self.ipv6list = []  # "
        self.ipv6dict = {}  # "

        if entrylist:
            l4 = []
            l6 = []
            for b,e in entrylist:
                assert b <= e
                if b.find(':') < 0:        # IPv4
                    b = to_long_ipv4(b)
                    e = to_long_ipv4(e)
                    l4.append((b,e))
                else:
                    b = to_long_ipv6(b)
                    e = to_long_ipv6(e)
                    bb = b % (256*256*256*256)
                    if bb == ipv4addrmask:
                        b -= bb
                        e -= bb
                        l4.append((b,e))
                    else:
                        l6.append((b,e))
            self._import_ipv4(l4)
            self._import_ipv6(l6)

    def __nonzero__(self):
        return bool(self.ipv4list or self.ipv6list)


    def append(self, ip_beg, ip_end = None):
        if ip_end is None:
            ip_end = ip_beg
        else:
            assert ip_beg <= ip_end
        if ip_beg.find(':') < 0:        # IPv4
            ip_beg = to_long_ipv4(ip_beg)
            ip_end = to_long_ipv4(ip_end)
            l = self.ipv4list
            d = self.ipv4dict
        else:
            ip_beg = to_long_ipv6(ip_beg)
            ip_end = to_long_ipv6(ip_end)
            bb = ip_beg % (256*256*256*256)
            if bb == ipv4addrmask:
                ip_beg -= bb
                ip_end -= bb
                l = self.ipv4list
                d = self.ipv4dict
            else:
                l = self.ipv6list
                d = self.ipv6dict

        p = bisect(l,ip_beg)-1
        if p >= 0:
            while p < len(l):
                range_beg = l[p]
                if range_beg > ip_end+1:
                    done = True
                    break
                range_end = d[range_beg]
                if range_end < ip_beg-1:
                    p += 1
                    if p == len(l):
                        done = True
                        break
                    continue
                # if neither of the above conditions is true, the ranges overlap
                ip_beg = min(ip_beg, range_beg)
                ip_end = max(ip_end, range_end)
                del l[p]
                del d[range_beg]
                break

        insort(l,ip_beg)
        d[ip_beg] = ip_end


    def _import_ipv4(self, entrylist):  #entrylist = sorted list of pairs of ipv4s converted to longs
        assert not self.ipv4list
        if not entrylist:
            return
        entrylist.sort()
        l = []
        b1,e1 = entrylist[0]
        for b2,e2 in entrylist:
            if e1+1 >= b2:
                e1 = max(e1,e2)
            else:
                l.append((b1,e1))
                b1 = b2
                e1 = e2
        l.append((b1,e1))
        self.ipv4list = [b for b,e in l]
        self.ipv4dict.update(l)

    def _import_ipv6(self, entrylist):  #entrylist = sorted list of pairs of ipv6s converted to longs
        assert not self.ipv6list
        if not entrylist:
            return
        entrylist.sort()
        l = []
        b1,e1 = entrylist[0]
        for b2,e2 in entrylist:
            if e1+1 >= b2:
                e1 = max(e1,e2)
            else:
                l.append((b1,e1))
                b1 = b2
                e1 = e2
        l.append((b1,e1))
        self.ipv6list = [b for b,e in l]
        self.ipv6dict.update(l)


    def includes(self, ip):
        if not (self.ipv4list or self.ipv6list):
            return False
        if ip.find(':') < 0:        # IPv4
            ip = to_long_ipv4(ip)
            l = self.ipv4list
            d = self.ipv4dict
        else:
            ip = to_long_ipv6(ip)
            bb = ip % (256*256*256*256)
            if bb == ipv4addrmask:
                ip -= bb
                l = self.ipv4list
                d = self.ipv4dict
            else:
                l = self.ipv6list
                d = self.ipv6dict
        for ip_beg in l[bisect(l,ip)-1:]:
            if ip == ip_beg:
                return True
            ip_end = d[ip_beg]
            if ip > ip_beg and ip <= ip_end:
                return True
        return False


    def read_rangelist(self, filename):
        """Read a list from a file in the format 'whatever:whatever:ip[-ip]
        (not IPv6 compatible at all)"""
        l = []
        with open(filename, 'r') as f:
            for line in f:
                fields = line.split()
                if not fields or fields[0][0] == '#':
                    continue

                iprange = fields[0].split(':')[-1]
                ip1, dash, ip2 = iprange.partition('-')
                if not ip2:
                    ip2 = ip1

                try:
                    ip1 = to_long_ipv4(ip1)
                    ip2 = to_long_ipv4(ip2)
                    assert ip1 <= ip2
                except:
                    print '*** WARNING *** could not parse IP range: '+iprange
                l.append((ip1,ip2))
        self._import_ipv4(l)


def is_ipv4(ip):
    return ip.find(':') < 0

def is_valid_ip(ip):
    try:
        if is_ipv4(ip):
            a = ip.split('.')
            assert len(a) == 4
            for i in a:
                chr(int(i))
            return True
        to_long_ipv6(ip)
        return True
    except:
        return False
