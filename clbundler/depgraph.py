import logging

class DepGraph:
    def __init__(self):
        self._graph = {}
        self._visited = {}
    
    def add(self, node, children):
        self._graph[node] = children
        for n in children:
            if not self._graph.has_key(n):
                self._graph[n] = []
    
    def traverse(self, callback):
        self._visited = dict.fromkeys(self._graph.keys(), False)
              
        for k in self._graph.keys():
            self._visit(k, callback)
    
    def deps(self, node):
        return self._graph[node]
        
    def requires(self, node):
        result = set()
        
        #first remove unnecessary nodes from the list
        for n in set(self._graph.keys()) - set([node]) - set(self.deps(node)):
            if node in self.deps(n) and node != n:
                result.add(n)
                result = result.union(self.requires(n))
        
        return result
        
    def _visit(self, node, callback):
        if not self._visited[node]:
            for n in self._graph[node]:
                if not self._visited[n]:
                    self._visit(n, callback)
                
            self._visited[node] = True
            callback(node)        
        