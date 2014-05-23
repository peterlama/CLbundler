import os
import imp
import logging
import config

_formula_cache = {}
_formula_kit_cache = {}

_default_search_path = [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Formula"))]
_default_search_path.append(os.path.join(_default_search_path[0], config.os_name()))

def _validate(formula):
    required_attrs = ["version", "source", "supported", "install"]
    for a in required_attrs:
        if not hasattr(formula, a):
            raise AttributeError
            
    setattr(formula, "name", formula.__name__)  
    
    if not hasattr(formula, "depends_on"):
        setattr(formula, "depends_on", [])
    if not hasattr(formula, "patches"):
        setattr(formula, "patches", [])
    
def _validate_kit(formula_kit):
    if not hasattr(formula_kit, "depends_on"):
        raise AttributeError
        
    setattr(formula_kit, "name", formula_kit.__name__)  
   
def get(name, search_path=[]):
    file_path = ""
    
    #name can be a path
    if os.path.isfile(name):
        file_path = name
        
    name = os.path.splitext(os.path.basename(name))[0]
    
    if _formula_cache.has_key(name):
        return _formula_cache[name]
    else:
        if file_path:
            module_info = imp.find_module(name, [os.path.dirname(file_path)])
        else:
            module_info = imp.find_module(name, search_path + _default_search_path)
            
        formula = imp.load_module(name, *module_info)
        _validate(formula)
        
        _formula_cache[name] = formula
        
        return formula
        
def get_kit(name, search_path=[]):
    path = ""

    #name can be a path
    if os.path.isdir(name):
        path = name
        
    name = os.path.basename(name)
    
    if _formula_kit_cache.has_key(name):
        return _formula_kit_cache[name]
    else:
        if path:
            module_info = imp.find_module(name, [os.path.dirname(path)])
        else:
            module_info = imp.find_module(name, search_path + _default_search_path)
        
        formula = imp.load_module(name, *module_info)
        _validate_kit(formula)
        
        _formula_kit_cache[name] = formula
        
        return formula
        
def dep_list_str(formula):
    """
    return string only version of the formula's dependency list
    """
    deps = []
    for d in formula.depends_on:
        if isinstance(d, dict):
            deps.append(d.keys()[0])
        elif isinstance(d, str):
            deps.append(d)
    return deps
    
def is_kit(formula):
    return hasattr(formula, "depends_on") and not hasattr(formula, "install")
