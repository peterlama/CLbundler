import os
import imp
import logging

import config
from formula import Formula
import exceptions

_formula_cache = {}

_formula_search_path = [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Formula"))]
_formula_search_path.append(os.path.join(_formula_search_path[0], config.os_name()))
_formula_search_path.extend(config.global_config().formula_dirs())

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
    if search_path is None:
        search_path = []
    #name can be a path
    if os.path.exists(name) and (name.count("/") or name.count("\\")):
        search_path = os.path.dirname(name)
        name = os.path.splitext(os.path.basename(name))[0]
    elif name.count(".") == 1 and not (name.count("/") or name.count("\\")):
        #formula is inside of a kit
        kit_name, name = name.split(".")
        search_path = []
        for p in _formula_search_path:
            search_path.append(os.path.join(p, kit_name))
            search_path.append(os.path.join(p, kit_name, config.os_name()))
    else:
        name = os.path.splitext(os.path.basename(name))[0]
        search_path.extend(_formula_search_path)
    
    if _formula_cache.has_key(name):
        return _formula_cache[name]
    else:
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
