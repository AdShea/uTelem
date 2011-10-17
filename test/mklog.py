#!/usr/bin/env python

from time import time
from sys import argv
from random import randint,choice

if __name__ == '__main__':
    t = time()
    pkts = dict([('{:08x}'.format(randint(0,2**11-1)),randint(1,8)) for x in xrange(24)])

    for idx in xrange(1000):
        header = choice(pkts.keys())
        print '{:.5f},{},{}'.format(t,header,','.join(['{:02x}'.format(randint(0,255)) for i in xrange(pkts[header])]))
        t = t + randint(5,30000) * 0.00001

