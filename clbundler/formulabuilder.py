import os
import logging
import time
import shutil

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
        
        build_dir = os.path.join(config.global_config().workspace_dir(),
                                     "build_{0}_{1}".format(bundle.toolchain, bundle.arch))
        config.global_config().set("Paths", "build", build_dir)
        
        if not os.path.isdir(build_dir):
            os.mkdir(build_dir)
        
        self._context.build_dir = build_dir
        
    def add_hook(self, hook, function):
        self._hook_functions[hook].add(function)
    
    def remove_hook(self, hook, function):
        self._hook_functions[hook].remove(function)
    
    def _call_hook_functions(self, hook):
        for f in self._hook_functions[hook]:
            f()
      
    def install(self, formula_spec, options):
        formula_name, formula_path = formulamanager.parse_specifier(formula_spec)
        
        if not self._bundle.is_installed(formula_name) or options.force:
            self._dep_graph = Graph()
            self._create_dep_graph(formula_name, formula_path)
            
            env.setup_env(self._context.toolchain, self._context.arch)
            self._context.env = env.env
            
            #install dependencies
            self._dep_graph.traverse(self._install, callback_args={"variant":options.variant})
            
            self._install(formula_name, **vars(options))
        else:
            print("{0} is already installed".format(formula_name))
        
    
    def uninstall(self, name, keep_dependent=False):
        if self._bundle.is_installed(name):
            dep_graph = Graph()
            installed = self._bundle.list_installed()
            
            for n in installed:
                dep_graph.add_node(n[0], self._bundle.deps(n[0]))
            
            node = dep_graph.get_node(name)
            
            if not keep_dependent and node.parents:
                #first uninstall packages that require this package
                logging.getLogger().info("The following packages depend on {0} "
                                         "and will also be uninstalled:".format(name))
                logging.getLogger().info(", ".join(node.parents))
                for n in node.parents:
                    logging.getLogger().info("Uninstalling {0}...".format(n))
                    self._bundle.uninstall(n)
            
            logging.getLogger().info("Uninstalling {0}...".format(name))
            self._bundle.uninstall(name)
            logging.getLogger().info("Done")
        else:
            print("{0} is not installed".format(name))
    
    def _install(self, formula_name, **kwargs):
        formula = formulamanager.get(formula_name, self._context)
        formula_options = {}
        force_install = False
        clean_src = False
        
        if kwargs.has_key("formula_options"):
            formula_options = kwargs["formula_options"]
        if kwargs.has_key("variant"):
            formula_options["variant"] = kwargs["variant"]
        if kwargs.has_key("force"):
            force_install = kwargs["force"]
        if kwargs.has_key("clean_src"):
            clean_src = kwargs["clean_src"]
        
        formula.set_options(formula_options)
        
        if not formula.is_kit and (force_install or not self._bundle.is_installed(formula.name)):
            if clean_src:
                build_src_dir = os.path.join(self._context.build_dir, "{0}-{1}".format(formula.name, formula.version))
                if os.path.exists(build_src_dir):
                    shutil.rmtree(build_src_dir)
            
            src_dir = sourcemanager.get_source(config.global_config().build_dir(), 
                                               formula.name, formula.version, formula.source)
            
            old_cwd = os.getcwd()
            os.chdir(src_dir)
            
            if formula.patches:
                path1 = os.path.join(formula.dir, "patches", formula.name)
                if formula.dir.endswith(config.os_name()):
                    path2 = os.path.normpath(os.path.join(formula.dir, "..", "patches", formula.name))
                else:
                    path2 = os.path.join(formula.dir, config.os_name(), "patches", formula.name)
                patch_dirs = [path1, path2]
                
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
            logging.getLogger().info("Building {0}...".format(formula.name))
            
            fileset = formula.build()
            
            self._call_hook_functions(self.hooks.post_build)
            logging.getLogger().info("Done")
            logging.getLogger().info("Installing {0}...".format(formula.name))
            
            self._bundle.install(formula.name, formula.version, formula.depends_on.keys(), fileset, force_install)
            
            self._call_hook_functions(self.hooks.post_install)
            logging.getLogger().info("Done")
            
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
        
        

