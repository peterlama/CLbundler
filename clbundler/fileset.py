from clbundler import exceptions

class FileSet(object):
    def __init__(self):
        self.categories = ["rel","dbg","dev"]
        self.files = {"rel":[], "dbg":[], "dev":[]}
        
    def add(self, patterns, dest, exclude_patterns=[], category="rel"):
        try:
            self.files[category].append((patterns, exclude_patterns, dest))
        except KeyError as e:
            raise exceptions.CLbundlerError("Unknown file category '{}'".format(e.message))
    
    def iter_items(self, category):
        if not self.files.has_key(category):
            raise exceptions.CLbundlerError("Unknown file category '{}'".format(e.message))
        return iter(self.files[category])
