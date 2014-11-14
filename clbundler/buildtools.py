import os

import system
from fileutils import makedirs

def configure(context, options=[]):
    args = ["--prefix=" + context.install_dir]
    args.extend(options)
    system.run_cmd("./configure", args)

def cmake_generator(toolchain, arch):
    """Return name of CMake generator for toolchain"""
    generator = ""
    if toolchain.startswith("vc"):
        if toolchain == "vc9":
            generator = "Visual Studio 9 2008"
        else:
            generator = "Visual Studio {0}".format(vc_version(toolchain))
        if arch == "x64":
            generator = generator + " Win64"
    else:
        generator = "Unix Makefiles"
        
    return generator

def cmake(context, options={}, build_dir=""):
    """Configure a CMake based project

    The current directory is assumed to be the top level source directory
    CMAKE_INSTALL_PREFIX will be set to context.install_dir
    
    Arguments:
    context -- BuildContext instance
    options -- dictionary of CMake cache variables
    build_dir -- the directory used for the build (defaults to ./cmake_build)
    """
    if not build_dir:
        build_dir = "cmake_build"
    
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
        
    os.chdir(build_dir)
    
    args = ["-D", "CMAKE_INSTALL_PREFIX=" + context.install_dir]
    for i in options.iteritems():
        args.extend(["-D", "=".join(i)])
    args.extend(["-G", cmake_generator(context.toolchain, context.arch)])
    args.append(os.path.relpath(".", build_dir))
    
    system.run_cmd("cmake", args)
    
    os.chdir("..")

def vc_version(toolchain):
    """Return the Visual C++ version from the toolchain string as an int"""
    if toolchain.startswith("vc"):
        return int(toolchain[2:])
        
def vc_version_year(toolchain):
    """Return the Visual C++ version year from the toolchain string"""
    if toolchain == "vc9":
        return "2008"
    elif toolchain == "vc10":
        return "2010"
    elif toolchain == "vc11":
        return "2012"
    elif toolchain == "vc12":
        return "2013"
    else:
        return ""
    
def vcproj_ext(toolchain):
    """Return file extension for Visual C++ projects"""
    vc_ver = vc_version(toolchain)
    if vc_ver > 9:
        return ".vcxproj"
    else:
        return ".vcproj"
    
def vcbuild(context, filepath, config, platform=None, use_env=False, extra=None, ignore_errors=False):
    """Build a Visual C++ project file or solution
    
    Uses vcbuild for vc9 and older, msbuild otherwise 
    
    Arguments:
    context -- BuildContext instance
    filepath -- path to project or solution
    config -- the solution configuration to use
    extras -- extra command line options to pass to vcbuild or msbuild
    ignore_errors -- ignore CalledProcessError or not
    """
    if platform is None:
        if context.arch == "x64":
            platform = "x64"
        else:
            platform = "Win32"
    if extra is None:
        extra = []
    
    use_env_opt = ""
    
    if int(vc_version(context.toolchain)) > 9:
        if use_env:
            use_env_opt = "/p:UseEnv=true"  
        system.run_cmd("msbuild", [filepath, "/m", "/nologo", "/verbosity:minimal",
                                   "/p:Configuration=" + config,
                                   "/p:Platform=" + platform, use_env_opt] + extra, 
                                   ignore_errors=ignore_errors)
    else: 
        if use_env:
            use_env_opt = "/useenv"        
        system.run_cmd("vcbuild", [filepath, "{0}|{1}".format(config, platform), use_env_opt] + extra, 
                       ignore_errors=ignore_errors)
    
def vcproj_upgrade(vcproj_file):
    new_name = os.path.splitext(vcproj_file)[0] + ".vcxproj"
    
    if not os.path.exists(new_name):
        system.run_cmd("vcupgrade", [vcproj_file])
    
    return new_name

def distutils(context):
    if context.os_name == "win":
        tmp_site_packages = context.install_dir + "\\Lib\site-packages"
        makedirs(tmp_site_packages, exist_ok=True)
        context.env["PYTHONPATH"] = tmp_site_packages
        context.env["INCLUDE"] += context.bundle_path + "\\include\python2.7;"
        context.env["LIB"] += context.bundle_path + "\\lib;"
    
    system.run_cmd("python", ["setup.py", "install", "--prefix=" + context.install_dir])
