import subprocess

class CLbundlerError(Exception):
    pass
    
class CommandNotFoundError(CLbundlerError):
    pass
    
class CalledProcessError(CLbundlerError, subprocess.CalledProcessError):
    def __init__(self, returncode, command):
        subprocess.CalledProcessError.__init__(self, returncode, command)
    
class FileNotFoundError(CLbundlerError):
    pass