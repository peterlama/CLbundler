import os
import imp
import logging
import traceback

import config
from formula import Formula
import exceptions

_formula_cache = {}

_default_search_path = [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Formula"))]
_default_search_path.append(os.path.join(_default_search_path[0], config.os_name()))
    
def _validate(formula, toolchain, arch):
    if not formula.is_kit:
        required_attrs = ["version", "source", "supported"]
        source_types = ["archive"]
        msg = "Formula '" + formula.name + "', {0}"
        for a in required_attrs:
            if not hasattr(formula, a):
                raise exceptions.FormulaError(msg.format("no attribute '{0}'".format(a)))
        
        if not formula.version:
            raise exceptions.FormulaError(msg.format("'version' is empty"))
            
        try:
            if formula.source["type"] not in source_types:
                raise exceptions.FormulaError(msg.format("value of source['type'] is "
                                                         "not one of {0}".format(source_types)))
            if not formula.source["url"]:
                raise exceptions.FormulaError(msg.format("value of source['url'] is empty"))
        except KeyError as e:
            raise exceptions.FormulaError(msg.format("'source' does not have key "
                                                     "'{0}'".format(e.message)))
            
        if (not formula.supported.has_key(toolchain) or 
            (formula.supported.has_key(toolchain) and not arch in formula.supported[toolchain])):
            raise exceptions.FormulaError(msg.format("does not support "
                                                     "{0}, {1}".format(toolchain, arch)))
    
def get(name, context, options={}, search_path=[]):
    file_path = ""
    
    #name can be a path
    if os.path.exists(name):
        file_path = name
        
    name = os.path.splitext(os.path.basename(name))[0]
    
    if _formula_cache.has_key(name):
        return _formula_cache[name]
    else:
        try:
            if file_path:
                module_info = imp.find_module(name, [os.path.dirname(file_path)])
            else:
                module_info = imp.find_module(name, search_path + _default_search_path)
        except ImportError:
            raise exceptions.FileNotFoundError("No formula named " + name)
            
        try:
            formula_module = imp.load_module(name, *module_info)
        except Exception as e:
            raise exceptions.FormulaExceptionError(traceback.format_exc())
        finally:
            #file object needs to be closed explicitly in the case of an exception
            if module_info[0]:
                module_info[0].close()
        
        try:
            cls = getattr(formula_module, name)
        except AttributeError:
            raise exceptions.exceptions.FormulaError("No class '{0}' in {1}".format(name, module_info[1]))

        if not isinstance(cls, type) or (isinstance(cls, type) and not issubclass(cls, Formula)):
            raise exceptions.exceptions.FormulaError("Object '{0}' in {1} is not a Formula "
                                          "subclass".format(name, module_info[1]))
            
        formula = cls(context, options)
        _validate(formula, context.toolchain, context.arch)
        
        _formula_cache[name] = formula
        
        return formula
