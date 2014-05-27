import os
import subprocess
import logging

from config import os_name
import env
import exceptions

_commands = {}

def _find_cmd(name, env_path):
    paths = env_path.split(os.pathsep)
    
    for path in paths:
        file_path = os.path.join(path, name)
        if os.path.isfile(file_path):
            return file_path
    raise exceptions.CommandNotFoundError(name + " could not be found by searching PATH")

def unix_path(path):
    drive_letter, path = os.path.splitdrive(path)
    if drive_letter:
        path = "/" + drive_letter[:-1] + path.replace("\\", "/")
    return path
    
def run_cmd(name, args=[], silent=False):
    """
    Run an executable file.
    Like a normal shell, name can be a path or a command that can be found by searching PATH.
    Special characters in args are escaped by the subprocess module
    If silent is true, output is dumped to devnull
    """
    if os.path.isfile(name):
        file_path = name
    else:
        if not _commands.has_key(name):
            if os_name() == "win" and not os.path.splitext(name)[1]:
                name = name + ".exe"
            file_path = _find_cmd(name, env.env["PATH"] + env.original_env["PATH"])
            _commands[name] = file_path
        else:
            file_path = _commands[name]
            
    cmd_line = [file_path] + args
    
    try:
        if silent:
            with open(os.devnull, 'wb') as devnull:
                subprocess.check_call(cmd_line, stdout=devnull,
                                      stderr=devnull, env=env.env)
        else:
            subprocess.check_call(cmd_line, env=env.env)
    except subprocess.CalledProcessError as e:
        raise exceptions.CalledProcessError(e.returncode, e.cmd)
    
def extract(filepath, dest, verbose=False):
    """
    Extract an archive using the appropriate system commands
    """
    args_7z = ["x", "-y", "-o" + dest]
    
    try:
        if os.path.splitext(filepath)[0].endswith(".tar"):
            try:
                args = ["-xf"]
                if verbose:
                    args = ["-xvf"]
                #tar can't handle Windows paths
                args.extend([unix_path(filepath), "-C", unix_path(dest)])
                
                run_cmd("tar", args)
            except exceptions.CommandNotFoundError:
                tar_filepath = os.path.join(dest, os.path.basename(os.path.splitext(filepath)[0]))
                
                run_cmd("7z", args_7z + [filepath], verbose)
                run_cmd("7z", args_7z + [tar_filepath], verbose)
                
                os.remove(tar_filepath)
                
        elif filepath.endswith(".zip"):
            try:
                args = []
                if not verbose:
                    args.append("-qq ")
                args.extend([filepath, "-d", dest])
                
                run_cmd("unzip", args)
            except exceptions.CommandNotFoundError:
                run_cmd("7z", args_7z + [filepath], verbose)

        else:
            #for all other types (example .7z) try 7z
            
            run_cmd("7z", args_7z + [filepath], verbose)

            
    except exceptions.CommandNotFoundError:
        #change message
        raise exceptions.CommandNotFoundError("Could not find a program for extracting file (unzip, tar, 7z)")
        
def patch(patches, path):
    """
    Convenience function for applying patches with GNU patch
    """
    if isinstance(patches, str):
        patches = [patches]
        
    for patch in patches:
        try:
            run_cmd("patch", ["-f", "-p1", "-d", path, "-i", patch])
        except exceptions.CalledProcessError:
            logging.getLogger().warning("Failed to apply patch: " + os.path.basename(patch))
