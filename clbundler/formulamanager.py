import os
import imp

_formula_cache = {}

_default_search_path = [os.path.join(os.path.dirname(__file__), "..", "Formula")]

class FormulaManager:
    @staticmethod
    def _find(name, search_path=[]):
        file_path = ""
        for path in search_path + default_search_path:
            if os.path.exists(os.path.join(path, name + ".py")):
                file_path = os.path.join(path, name + ".py")
        return file_path
    
    @staticmethod    
    def get(name, search_path=[]):
        file_path = ""

        #name can be a path
        if os.path.isfile(name):
            file_path = name
            
        name = os.path.splitext(os.path.basename(file_path))[0]
        
        if _formula_cache.has_key(name):
            return _formula_cache[name]
        else:
            if not file_path:
                file_path = FormulaManager._find(name, search_path)
            
            formula = imp.load_source(name, file_path)
            _formula_cache[name] = formula
            
            return formula
    
        