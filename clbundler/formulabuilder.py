import os
import logging
import formulamanager
from depgraph import DepGraph

class FormulaBuilder:
    def __init__(self, bundle, formula):
        self._bundle = bundle
        self._dep_graph = DepGraph()
        self._create_dep_graph(formula)
        
    def install(self):
        self._dep_graph.traverse(lambda name: formulamanager.get(name).install())
        
    def _create_dep_graph(self, formula):
        def _add_node(graph, formula):
            deps = formulamanager.dep_list_str(formula)
            for n in deps:
                _add_node(graph, formulamanager.get(n, [os.path.dirname(formula.__file__)]))
                
            self._dep_graph.add(formula.name, deps)
        
        if not formulamanager.is_kit(formula):
            self._dep_graph.add(formula.name, formulamanager.dep_list_str(formula))        
        
        for n in formulamanager.dep_list_str(formula):
            #logging.getLogger().debug(os.path.dirname(formula.__file__))
            _add_node(self._dep_graph, formulamanager.get(n, [os.path.dirname(formula.__file__)]))
        