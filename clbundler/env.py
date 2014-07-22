import os
import sys
import subprocess

from config import os_name, global_config
import exceptions

original_env = os.environ.copy()
env = os.environ.copy()

def setup_env(toolchain, arch):
    """Set up environment for specified toolchain"""
    global env
    env = os.environ.copy()
    #set PATH to minimum to control exactly what software is found.
    path = ""
    if os_name() == "win":
        path = "C:\\Windows\\system32;C:\\Windows;C:\\Windows\\System32\\Wbem;"
    elif os_name() == "mac":
        path = "/usr/bin:/bin:/usr/sbin:/sbin:"
    
    if global_config().current_bundle():    
        path = os.path.join(global_config().current_bundle(), "bin") + os.pathsep + path
        env["CMAKE_PREFIX_PATH"] = global_config().current_bundle()
        
    env["PATH"] = path
    
    if toolchain.startswith("vc"):
        setup_env_vc(toolchain[2:], arch)
    
def environ_from_bat(bat_file, args=""):
    """Get environment modified by .bat file"""
    
    #call 'set' in the same shell as the '.bat' file is run, and parse output
    cmd = '"{0}" {1} && echo OutputSeparator && set'.format(bat_file, args)
    output = subprocess.check_output(cmd, shell=True, env=env)
    env_dump = output.split("OutputSeparator")[1]

    new_environ = {}

    for line in env_dump.strip().split("\r\n"):
        pair = line.split("=")
        new_environ[pair[0].upper()] = pair[1]
    
    return new_environ
    
def setup_env_vc(version, arch):
    """Set up Visual Studio build environment."""
    global env
    comntools = "VS{0}0COMNTOOLS".format(version)
    
    try:
        comntools_path = env[comntools]
    except KeyError:
        raise exceptions.BuildConfigError("Could not find toolchain: vc" + version,
                                          "No environment variable named '{0}'".format(comntools))
        
    vc_dir = os.path.normpath(comntools_path + "..\\..\\VC")
    env_bat = vc_dir + "\\vcvarsall.bat"
    env64_bat = None
    if os.path.exists(vc_dir + "\\bin\\vcvars64.bat"):
        env64_bat = vc_dir + "\\bin\\vcvars64.bat"
    
    if not os.path.exists(env_bat):
        raise exceptions.BuildConfigError("Could not find toolchain: vc" + version,
                                          "File does not exist: " + env_bat)
        
    if arch == "x64":
        if env64_bat is not None:
            env = environ_from_bat(env64_bat)
        elif subprocess.check_output([env_bat, "amd64"]) == '':
            env = environ_from_bat(env_bat, "amd64")
        elif subprocess.check_output([env_bat, "x86_amd64"]) == '':
            env = environ_from_bat(env_bat, "x86_amd64")
        else:
            raise exceptions.BuildConfigError("Could not find toolchain: vc" + version + " for x64")
    else:
        #vcvarsall.bat should allways be able to find x86 tools
        env = environ_from_bat(env_bat, "x86")
        