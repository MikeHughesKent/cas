# -*- coding: utf-8 -*-
"""
Sets paths needed for examples to work.

"""

import sys, os
testdir = os.path.dirname(__file__)
srcdir = '../src/'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

srcdir = '../src/cameras'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

srcdir = '../src/widgets'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

srcdir = '../src/threads'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))
