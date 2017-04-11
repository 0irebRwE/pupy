#!/usr/bin/env python
# -*- coding: utf-8 -*-

import memorpy
import re
import os

def try_int(x):
    try:
        return int(x)
    except:
        return x

def find_strings(targets, min_length=4, max_length=51, omit='isxr'):
    if not targets:
        return {}

    if type(targets) == (str, int):
        targets = [ targets ]

    targets = set([ try_int(x) for x in targets ])
    results = {}

    printable = re.compile('^[\x20-\x7e]{{{},{}}}$'.format(min_length, max_length))

    for process in memorpy.Process.list():
        if not (
            os.path.basename(process.get('name')) in targets or process.get('pid') in targets
        ):
            continue

        strings = []
        results[process.get('pid')] = {
            'name': process.get('name'),
            'strings': strings
        }

        mw = memorpy.MemWorker(pid=process.get('pid'))
        duplicates = set()
        for _, (cstring,) in mw.mem_search('([^\x00]+)', ftype='groups', optimizations=omit):
            if printable.match(cstring):
                if not cstring in duplicates:
                    duplicates.add(cstring)
                    strings.append(cstring)

    return results

if __name__=="__main__":
    import sys
    for pid, strings in find_strings(sys.argv[1].split(',')).iteritems():
        print 'pid: ', pid
	print
	for s in strings:
            print s
	print
