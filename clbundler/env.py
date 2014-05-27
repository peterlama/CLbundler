import os
import sys

from config import os_name, global_config

original_env = os.environ.copy()
env = os.environ.copy()

def setup_env():
    env = os.environ.copy()
    #set PATH to minimum to control exactly what software is found.
    path = ""
    if os_name() == "win":
        path = "C:\\Windows\\system32;C:\\Windows;C:\\Windows\\System32\\Wbem;"
    elif os_name() == "mac":
        path = "/usr/bin:/bin:/usr/sbin:/sbin:"
    
    if global_config().current_bundle():    
        path = os.path.join(global_config().current_bundle(), "bin") + os.pathsep + path
        
    env["PATH"] = path
    