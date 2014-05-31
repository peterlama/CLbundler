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

class FormulaError(CLbundlerError):
    pass
    
class FormulaExceptionError(FormulaError):
    pass
    
class InvalidUrlError(CLbundlerError):
    pass
    
class SourceArchiveError(CLbundlerError):
    pass
