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
    #TODO: check if path is valid bundle
    config.global_config().set("Bundle", "path", path)
    config.global_config().write()

def cmd_new(path, toolchain, arch):
    fpath = path.format(platform=config.os_name(), toolchain=toolchain, arch=arch)
    if fpath.split(os.sep)[0] == fpath:
        fpath = os.path.join(config.global_config().root_dir(), fpath)

    bundle = LibBundle()
    bundle.create(fpath, config.os_name(), toolchain, arch)

    cmd_set(fpath)

def cmd_install(name, interactive=False):
    bundle = LibBundle()
    bundle.load(config.global_config().current_bundle())

    builder = FormulaBuilder(bundle)
    
    if interactive:
        def _start_shell():
            print("Type 'exit' to continue with the installation, 'exit 1' to abort")
            try:
                system.shell()
            except exceptions.CalledProcessError:
                raise exceptions.AbortOperation
        
        builder.add_hook(builder.hooks.pre_build, _start_shell)
    
    try:    
        builder.install(name)
    except exceptions.AbortOperation:
        print("Installation Aborted")

def cmd_uninstall(name):
    bundle = LibBundle()
    bundle.load(config.global_config().current_bundle())

    #name could be a path
    package_name = os.path.splitext(os.path.basename(name))[0]
    bundle.uninstall(package_name)
