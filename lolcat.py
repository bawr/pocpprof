#!/usr/bin/env python
# function cat { ~/Public/pocpprof/lolcat.py; unset cat; }

import io
import os
import re
import sys
import termios

import psutil

rd = open('/home/bawr/Public/pocpprof/main_base.py', 'rb').read()

pr = psutil.Process()
pt = pr.terminal()
ft = open(pt, 'r+b', 0)
fd = ft.fileno()

tc_old = termios.tcgetattr(fd)
tc_new = termios.tcgetattr(fd)

try:
    tc_new[3] = tc_new[3] &~(termios.ICANON | termios.ECHO)
    termios.tcsetattr(fd, termios.TCSADRAIN, tc_new)
    if sys.stdout.isatty():
        fo = io.BytesIO()
    else:
        fo = os.fdopen(sys.stdout.fileno(), 'wb', 0)
    while (b'\x04' != ft.read(1)):
        for _ in range(2):
            fi = re.match(b'([* ]+)|([a-z_A-Z]+)|([0-9.]+)|(.?)', rd, re.ASCII | re.DOTALL).span()[1]
            fc, rd = rd[:fi], rd[fi:]
            ft.write(fc)
            fo.write(fc)
except KeyboardInterrupt:
    pass
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, tc_old)
