import subprocess
import traceback

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
    def __init__(self, formula, message):
        self.formula = formula
        self.message = message
    def __str__(self):
        return "Formula '{0}': {1}".format(self.formula, self.message)
    
class FormulaExceptionError(FormulaError):
    def __init__(self, formula):
        super(FormulaExceptionError, self).__init__(formula, "\n" + traceback.format_exc())
    
class InvalidUrlError(CLbundlerError):
    pass
    
class SourceArchiveError(CLbundlerError):
    pass

class BundleError(CLbundlerError):
    pass
    
class BuildConfigError(CLbundlerError):
    def __init__(self, message, detail=""):
        self.message = message
        self.detail = detail
    def __str__(self):
        if self.detail:
            return self.message + "\n\n" + self.detail
        return self.message
