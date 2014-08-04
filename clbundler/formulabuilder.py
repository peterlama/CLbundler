import os
import logging
import time

from enum import Enum
import formulamanager
import sourcemanager
import exceptions
import env
from graph import Graph
import config 
import fileutils

class BuildContext:
    def __init__(self, bundle_path, toolchain, arch):
        self.bundle_path = bundle_path
        self.toolchain = toolchain
        self.arch = arch
        self.os_name = config.os_name()
        self.env = env.env
        self.workspace_dir = config.global_config().workspace_dir()
        self.install_dir = os.path.join(self.workspace_dir, "tmp_install")
        
class FormulaBuilder:
    def __init__(self, bundle):
        self._bundle = bundle
        self._context = BuildContext(bundle.path, bundle.toolchain, bundle.arch)
        
        self.hooks = Enum("pre_build","post_build", "post_install")
        self._hook_functions = {self.hooks.pre_build:set(), 
                                self.hooks.post_build:set(),
                                self.hooks.post_install:set()}
        
        workspace_dir = os.path.join(config.global_config().workspace_dir(),
                                     "build_{0}_{1}".format(bundle.toolchain, bundle.arch))
        config.global_config().set("Paths", "workspace", workspace_dir)
        
        if not os.path.isdir(workspace_dir):
            os.mkdir(workspace_dir)
        
        self._context.workspace_dir = workspace_dir
        
    def add_hook(self, hook, function):
        self._hook_functions[hook].add(function)
    
    def remove_hook(self, hook, function):
        self._hook_functions[hook].remove(function)
    
    def _call_hook_functions(self, hook):
        for f in self._hook_functions[hook]:
            f()
            
    def install(self, formula_spec, force=False):
        formula_name, formula_path = formulamanager.parse_specifier(formula_spec)
        
        self._dep_graph = Graph()
        self._create_dep_graph(formula_name, formula_path)
        
        env.setup_env(self._context.toolchain, self._context.arch)
        self._context.env = env.env
        
        #install dependencies
        self._dep_graph.traverse(self._install)
        
        self._install(formula_name, force)
    
    def uninstall(self, name):
        dep_graph = Graph()
        installed = self._bundle.installed()
        
        for n in installed:
            dep_graph.add_node(n, self._bundle.deps(n))
        
        node = dep_graph.get_node(name)
        #first uninstall packages that require this package
        for n in node.parents:
            self._bundle.uninstall(n)
        
        self._bundle.uninstall(name)
        
    def _install(self, formula_name, force=False):
        formula = formulamanager.get(formula_name, self._context)
        if not formula.is_kit and (force or not self._bundle.is_installed(formula.name)):
            src_dir = sourcemanager.get_source(config.global_config().workspace_dir(), 
                                               formula.name, formula.version, formula.source)
            
            old_cwd = os.getcwd()
            os.chdir(src_dir)
            
            if formula.patches:
                path1 = os.path.join(formula.dir, "patches", formula.name)
                path2 = os.path.join(formula.dir, "..", "patches", formula.name)
                patch_dirs = [os.path.join(path1, self._bundle.toolchain), path1,
                              os.path.join(path2, self._bundle.toolchain), path2]
                
                sourcemanager.patch_source(formula.patches, patch_dirs, src_dir) 
            
            #make sure we have clean install dir for each formula 
            if os.path.exists(self._context.install_dir):
                fileutils.remove(self._context.install_dir)
            try:
                os.mkdir(self._context.install_dir)
            except OSError:
                #On Windows, it is sometimes necessary to wait a little after deleting a 
                #directory before creating it again
                time.sleep(0.01)
                os.mkdir(self._context.install_dir)
                
            self._call_hook_functions(self.hooks.pre_build)
            
            fileset = formula.build()
            
            self._call_hook_functions(self.hooks.post_build)
            
            self._bundle.install(formula.name, formula.version, formula.depends_on.keys(), fileset, force)
            
            self._call_hook_functions(self.hooks.post_install)
            
            os.chdir(old_cwd)

    def _create_dep_graph(self, formula_name, formula_path=[]):
        def _add_node(graph, formula):
            for dep_name, options in formula.depends_on.iteritems():
                dep_formula = formulamanager.get(dep_name, self._context, options, formula_path)
                _add_node(self._dep_graph, dep_formula)
                
            self._dep_graph.add_node(formula.name, formula.depends_on.keys())
          
        formula = formulamanager.get(formula_name, self._context, search_path=formula_path)
        for dep_name, options in formula.depends_on.iteritems():
            _add_node(self._dep_graph, formulamanager.get(dep_name, self._context, options, 
                                                          formula_path))
        
        

