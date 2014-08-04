import logging

class Node:
    def __init__(self, name, children=None, parents=None):
        self.name = name
        if children is None:
            children = set()
        if parents is None:
            parents = set()
        self.children = children
        self.parents = parents
        self.marked = False
    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return hash(self.name)

class Graph:
    def __init__(self):
        self._graph = {}
    
    def add_node(self, name, children=None, parents=None):
        """Add a node to the graph.

        If there is node with the same name already in the graph, children and 
        parents will be added its child and parent sets.
        """
        if children is None:
            children = set()
        if parents is None:
            parents = set()
        if not isinstance(children, set):
            children = set(children)
        if not isinstance(parents, set):
            parents = set(parents)
        
        if self._graph.has_key(name):
            if children:
                self._graph[name].children = self._graph[name].children.union(children)
            if parents:
                self._graph[name].parents = self._graph[name].children.union(parents)
        else:
            node = Node(name, children, parents)
            self._graph[name] = node
            if children:
                for n in children:
                    if not self.has_node(n):
                        self._graph[n] = Node(n)
                    self._graph[n].parents.add(name)
            if parents:
                for n in parents:
                    if not self.has_node(n):
                        self._graph[n] = Node(n)
    
    def get_node(self, name):
        if self.has_node(name):
            return self._graph[name]
        return None
    
    def has_node(self, name):
        return self._graph.has_key(name)
    
    def roots(self):
        """Return a list of the nodes that do not have any parents."""
        root_nodes = []
        for k in self._graph.keys():
            if not self._graph[k].parents:
                root_nodes.append(self._graph[k])
        return root_nodes
    
    def traverse(self, callback=None, callback_args=[], start_nodes=[]):
        """Perform a depth first traversal of the graph."""
        for k in self._graph.keys():
            self._graph[k].marked = False
        
        if not start_nodes:
            start_nodes = self._graph.keys()
              
        for n in start_nodes:
            self._visit(n, callback, callback_args)
        
    def _visit(self, name, callback=None, callback_args=[]):
        if not self._graph[name].marked:
            for n in self._graph[name].children:
                if not self._graph[n].marked:
                    self._visit(n, callback, callback_args)
                
            self._graph[name].marked = True
            if callback:
                callback(name, *callback_args)        

