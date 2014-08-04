import os
import imp
import logging

import config
from formula import Formula
import exceptions

_formula_cache = {}

_default_search_path = [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Formula"))]
_default_search_path.append(os.path.join(_default_search_path[0], config.os_name()))
_default_search_path.extend(config.global_config().formula_dirs())

def _find_formula(name):
    """Find the location of a formula file or kit"""
    path = None
    
    for p in _default_search_path:
        kit = os.path.join(p, name)
        formula = os.path.join(p, name, ".py")
        if os.path.exists(kit) or os.path.exists(formula):
            path = p
            break
    
    if path is None:
        raise exceptions.FileNotFoundError("No formula named " + name)

    return path

def _validate(formula, toolchain, arch):
    if not formula.is_kit:
        required_attrs = ["version", "source", "supported"]
        source_types = ["archive"]
        
        for a in required_attrs:
            if not hasattr(formula, a):
                raise exceptions.FormulaError(formula.name, "no attribute '{0}'".format(a))
        
        if not formula.version:
            raise exceptions.FormulaError(formula.name, "'version' is empty")
            
        try:
            if formula.source["type"] not in source_types:
                raise exceptions.FormulaError(formula.name, "value of source['type'] is "
                                                            "not one of {0}".format(source_types))
            if not formula.source["url"]:
                raise exceptions.FormulaError(formula.name, "value of source['url'] is empty")
        except KeyError as e:
            raise exceptions.FormulaError(formula.name, "'source' does not have key "
                                                        "'{0}'".format(e.message))
            
        if (not formula.supported.has_key(toolchain) or 
            (formula.supported.has_key(toolchain) and not arch in formula.supported[toolchain])):
            raise exceptions.FormulaError(formula.name, "does not support "
                                                        "{0}, {1}".format(toolchain, arch))


    
def get(name, context, options={}, search_path=None):
    if _formula_cache.has_key(name):
        return _formula_cache[name]
    
    if search_path is None:
        search_path = _default_search_path
    
    try:
        module_info = imp.find_module(name, search_path)
    except ImportError:
        raise exceptions.FileNotFoundError("No formula named " + name)
        
    try:
        formula_module = imp.load_module(name, *module_info)
    except Exception as e:
        raise exceptions.FormulaExceptionError(name)
    finally:
        #file object needs to be closed explicitly in the case of an exception
        if module_info[0]:
            module_info[0].close()
    
    try:
        cls = getattr(formula_module, name)
    except AttributeError:
        raise exceptions.FormulaError(name, "no class '{0}' "
                                            "in {1}".format(name, module_info[1]))

    if not isinstance(cls, type) or (isinstance(cls, type) and not issubclass(cls, Formula)):
        raise exceptions.FormulaError(name, "object '{0}' in {1} is not a Formula "
                                            "subclass".format(name, module_info[1]))
        
    formula = cls(context, options)
    _validate(formula, context.toolchain, context.arch)
    
    _formula_cache[name] = formula
    
    return formula

def parse_specifier(formula_spec):
    """Return the name and location of the formula specified by formula_spec.

    formula_spec can be:
        - a path to the formula file or kit (if it is a relative path, it must 
          have at least one slash)
        - <kit name>.<formula name> to specify a formula located inside a kit
        - a formula name
    """
    formula_name = ""
    search_path = []
    
    if formula_spec.count(os.sep):
        #formula_spec is a path
        search_path.append(os.path.dirname(formula_spec))
        formula_name = os.path.splitext(os.path.basename(formula_spec))[0]
    elif formula_spec.count(".") == 1 and not formula_spec.count(os.sep):
        #formula_spec is in the form: <kit name>.<formula name>
        kit_name, formula_name = formula_spec.split(".")
        path = _find_formula(kit_name)
        search_path.append(os.path.join(path, kit_name))
        search_path.append(os.path.join(path, kit_name, config.os_name()))
    else:
        #formula_spec is just the formula name
        formula_name = formula_spec
        path = _find_formula(formula_name)
        search_path.append(path)
        formula_path = os.path.join(path, formula_name)
        if os.path.isdir(formula_path):
            #add kit directories as well
            search_path.append(formula_path)
            search_path.append(os.path.join(formula_path, config.os_name()))
    
    return formula_name, search_path

