import os
import config
from bundle import LibBundle

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

def cmd_install_kit(kit_name):
    bundle = LibBundle()
    bundle.load(config.global_config().current_bundle())
    
    builder = FormulaKitBuilder(bundle, kit_name)
    builder.build()
    builder.install()
    
def cmd_install(formula_name):
    bundle = LibBundle()
    bundle.load(config.global_config().current_bundle())
    
    builder = FormulaBuilder(bundle, formula_name)
    builder.build()
    builder.install()

def cmd_uninstall(formula_name):
    bundle = LibBundle()
    bundle.load(config.global_config().current_bundle())

    builder = FormulaBuilder(bundle, formula_name)
    builder.uninstall()