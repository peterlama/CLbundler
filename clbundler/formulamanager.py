import os
import imp
import logging

import config
from formula import Formula

_formula_cache = {}

_default_search_path = [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Formula"))]
_default_search_path.append(os.path.join(_default_search_path[0], config.os_name()))

def _validate(formula):
    if not formula.is_kit:
        required_attrs = ["version", "source", "supported", "build"]
        for a in required_attrs:
            if not hasattr(formula, a):
                raise AttributeError
   
def get(name, context, options={}, search_path=[]):
    file_path = ""
    
    #name can be a path
    if os.path.exists(name):
        file_path = name
        
    name = os.path.splitext(os.path.basename(name))[0]
    
    if _formula_cache.has_key(name):
        return _formula_cache[name]
    else:
        if file_path:
            module_info = imp.find_module(name, [os.path.dirname(file_path)])
        else:
            module_info = imp.find_module(name, search_path + _default_search_path)
        
        try:
            formula_module = imp.load_module(name, *module_info)
        finally:
            #file object needs to be closed explicitly in the case of an exception
            if module_info[0]:
                module_info[0].close()
        
        #todo: check attrs        
        formula = getattr(formula_module, name)(context, options)
        
        if formula.is_kit:
            _validate(formula)
        
        _formula_cache[name] = formula
        
        return formula
