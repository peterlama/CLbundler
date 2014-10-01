from __future__ import print_function
import os
import logging

import config
from bundle import LibBundle
from formulabuilder import FormulaBuilder
import formulamanager
import system
import exceptions

def cmd_set(path):
    #raises an exception if path is not a valid bundle
    bundle = LibBundle().load(path)
    
    config.global_config().set("Bundle", "path", path)
    config.global_config().write()

def cmd_new(path, toolchain, arch):
    fpath = path.format(platform=config.os_name(), toolchain=toolchain, arch=arch)
    if fpath.split(os.sep)[0] == fpath:
        fpath = os.path.join(config.global_config().root_dir(), fpath)

    bundle = LibBundle()
    bundle.create(fpath, config.os_name(), toolchain, arch)

    cmd_set(fpath)

def cmd_install(formula_spec, options):
    bundle = LibBundle()
    bundle.load(config.global_config().current_bundle())

    builder = FormulaBuilder(bundle)
    
    if options.interactive:
        def _start_shell():
            print("Type 'exit' to continue with the installation, 'exit 1' to abort")
            try:
                system.shell()
            except exceptions.CalledProcessError:
                raise exceptions.AbortOperation
        
        builder.add_hook(builder.hooks.pre_build, _start_shell)
    
    try:
        builder.install(formula_spec, options)
    except exceptions.AbortOperation:
        print("Installation Aborted")

def cmd_uninstall(package_name, keep_dependent=False):
    bundle = LibBundle()
    bundle.load(config.global_config().current_bundle())
    builder = FormulaBuilder(bundle)
    
    builder.uninstall(package_name, keep_dependent)

def cmd_archive(path=None):
    if path is None:
        path = os.path.dirname(config.global_config().current_bundle())
    
    bundle_name = os.path.basename(config.global_config().current_bundle())
    archive_path = os.path.join(path, bundle_name)
    
    if config.os_name() == "win":
        try:
            system.run_cmd("7z", ["a", "-r", "-x!*.pyc", 
                           archive_path + ".7z", 
                           config.global_config().current_bundle()])
        except exceptions.CalledProcessError as e:
            if e.returncode != 1:
                raise
    else:
        system.run_cmd("zip", ["-r", "-x", "*.pyc", 
                               archive_path + ".zip", 
                               config.global_config().current_bundle()])

def cmd_set_formula_path(path, append=False):
    if append:
        old_value = config.global_config().get("Paths", "formula_dirs")
        if not old_value.endswith(os.pathsep):
            old_value += os.pathsep
        config.global_config().set("Paths", "formula_dirs", old_value + path)
    else:
        config.global_config().set("Paths", "formula_dirs", path)
        
    config.global_config().write()
