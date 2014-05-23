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
    
    def depends_on(self, n):
        return self._graph[n]
        
    def required_by(self, n):
        result = []
        for k in self._graph.keys():
            if n in self._graph[k]:
                 result.append(k)
        return result
        
    def _visit(self, node, callback):
        if not self._visited[node]:
            for n in self._graph[node]:
                if not self._visited[n]:
                    self._visit(n, callback)
                
            self._visited[node] = True
            callback(node)        
        