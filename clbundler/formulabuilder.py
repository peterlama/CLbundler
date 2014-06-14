import os
import logging

from enum import Enum
import formulamanager
import sourcemanager
import exceptions
import env
from depgraph import DepGraph
import config 
import fileutils

class BuildContext:
    def __init__(self, bundle_path, toolchain, arch):
        self.bundle_path = bundle_path
        self.toolchain = toolchain
        self.arch = arch
        self.os_name = config.os_name()
        self.env = env.env
        self.install_dir = os.path.join(config.global_config().get("Paths", "workspace"),
                                        "tmp_install")
        
class FormulaBuilder:
    def __init__(self, bundle):
        self._bundle = bundle
        self._context = BuildContext(bundle.path, bundle.toolchain, bundle.arch)
        
        self.hooks = Enum("pre_build","post_build", "post_install")
        self._hook_functions = {self.hooks.pre_build:set(), 
                                self.hooks.post_build:set(),
                                self.hooks.post_install:set()}
        
    def add_hook(self, hook, function):
        self._hook_functions[hook].add(function)
    
    def remove_hook(self, hook, function):
        self._hook_functions[hook].remove(function)
    
    def _call_hook_functions(self, hook):
        for f in self._hook_functions[hook]:
            f()
            
    def install(self, formula_name):
        formula = formulamanager.get(formula_name, self._context)
        
        self._dep_graph = DepGraph()
        self._create_dep_graph(formula)
        
        env.setup_env(self._context.toolchain, self._context.arch)
        self._context.env = env.env
        #install dependencies
        self._dep_graph.traverse(self._install)
        
        self._install(formula_name)
        
    def _install(self, formula_name):
        formula = formulamanager.get(formula_name, self._context)
        if not formula.is_kit and not self._bundle.is_installed(formula.name):
            build_dir_name = "build_{0}_{1}".format(self._bundle.toolchain, self._bundle.arch)
            build_dir = os.path.join(config.global_config().workspace_dir(), build_dir_name)
            if not os.path.exists(build_dir):
                os.mkdir(build_dir)
                
            src_dir = sourcemanager.get_source(build_dir, formula.name, formula.version, formula.source)
            
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
            
            self._call_hook_functions(self.hooks.pre_build)
            
            fileset = formula.build()
            
            self._call_hook_functions(self.hooks.post_build)
            
            self._bundle.install(formula.name, formula.version, formula.depends_on.keys(), fileset)
            
            self._call_hook_functions(self.hooks.post_install)
            
            os.chdir(old_cwd)

    def _create_dep_graph(self, formula):
        def _add_node(graph, formula):
            for dep_name, options in formula.depends_on.iteritems():
                logging.getLogger().debug(formula.dir)
                _add_node(graph, formulamanager.get(dep_name, self._context, options, 
                                                    [formula.dir]))
                
            self._dep_graph.add(formula.name, formula.depends_on.keys())
        
        for dep_name, options in formula.depends_on.iteritems():
            #logging.getLogger().debug(formula.dir)
            _add_node(self._dep_graph, formulamanager.get(dep_name, self._context, options, 
                                                          [formula.dir]))
        