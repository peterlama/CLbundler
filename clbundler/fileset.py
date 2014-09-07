import os

from clbundler import exceptions
from enum import Enum

Categories = Enum("build", "build_dbg", "run", "run_dbg")

class FileSet(object):
    def __init__(self):
        self.files = dict([(c, []) for c in Categories])
        
    def add(self, patterns, dest, exclude=[], category=Categories.run):
        try:
            patterns = [os.path.abspath(p) for p in patterns if not os.path.isabs(p)]
            exclude = [os.path.abspath(p) for p in exclude if not os.path.isabs(p)]
            self.files[category].append((patterns, exclude, dest))
        except KeyError as e:
            raise exceptions.CLbundlerError("Unknown file category '{}'".format(e.message))
    
    def iter_items(self, category):
        if not self.files.has_key(category):
            raise exceptions.CLbundlerError("Unknown file category '{}'".format(e.message))
        return iter(self.files[category])
