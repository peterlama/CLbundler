import os
import sys
import logging

from fileset import Categories, FileSet
import system
from buildtools import *

class Formula(object):
    def __init__(self, context, options={}):
        self.context = context
        self.name = type(self).__name__
        self.dir = os.path.abspath(
            os.path.dirname(sys.modules[type(self).__module__].__file__))
        self.is_kit = False
        
        self.set_options(options)
        
        self.depends_on = {}
        self.patches = []
        
    def set_options(self, options):
        for k in options.keys():
            if hasattr(self, k):
                setattr(self, k, options[k])
            else:
                logging.getLogger().debug("Formula '{0}' has no option "
                                          "'{1}'".format(self.name, k))
                
    def add_deps(self, deps):
        for d in deps:
            if isinstance(d, str):
                self.depends_on[d] = {}
            elif isinstance(d, dict):
                self.depends_on.update(d)
            else:
                logging.getLogger().debug("Unsupported type in dependency list "
                                          "for formula '{0}'".format(self.name))
