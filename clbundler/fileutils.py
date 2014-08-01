import os
import errno
import shutil
import fnmatch
from glob import has_magic

def makedirs(path, mode=0o777, exist_ok=False):
    """Create a directory, and ancestors if necessary.
    
    If exists_ok is True, no exception is raised when path exists.
    Mimics behaviour of os.makedirs in python 3.2.
    """
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST:
            raise

def rmtree_onerror(func, path, exc):
    """Handle deleting read-only files on windows."""
    import stat
    excvalue = exc[1]
    if func in (os.rmdir, os.remove):
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO) # 0777
        func(path)
    else:
        raise
        
def remove(path):
    """Remove a directory or a file."""
    if os.path.isdir(path):
        shutil.rmtree(path, onerror=rmtree_onerror)
    else:
        os.remove(path)
    
def copy(src, dest, parents=False, replace=False, ignore=None):
    """Copy a directory or file to dest.
    
    If parents is True, create ancestor directories if they do not exist.
    
    If replace is True and src is a directory, first remove dest if it exists.
    Files will always be overwritten. 
    
    ignore should be function that can be used as shutil.copytree() ignore argument
    """
    if parents:
        makedirs(os.path.dirname(dest), exist_ok=True)
        
    if os.path.isdir(src):
        if replace:
            if os.path.exists(dest):
                remove(dest)
        
        shutil.copytree(src, dest, symlinks=True, ignore=ignore)
    else:
        if os.path.islink(src):
            if os.path.isdir(dest):
                dest = os.path.join(dest, os.path.basename(src))
            if os.path.exists(dest):
                remove(dest)
            os.symlink(os.readlink(src), dest)
        else:
            shutil.copy(src, dest)

def copy_ignore(patterns):
    """Return a function that can be used as shutil.copytree() ignore argument.
    
    All names that match one of the patterns according to match(), will be ignored.
    Note: the full path has to match, not just the name.
    """
    def _ignore(path, names):
        ignored_names = []
        for n in names:
            if match_list(os.path.join(path, n), patterns):
                ignored_names.append(n)
        return set(ignored_names)
    return _ignore
    
def separate_path(path):
    """Separate a path into its components"""
    path = path.rstrip("/").rstrip("\\")

    components = []
    #don't use regular string split so that we don't have to be strict on the format 
    #of the path
    dirname, basename = os.path.split(path)
    while basename:
        components.append(basename)
        dirname, basename = os.path.split(dirname)
    components.reverse()
    
    return components

def match(path, pattern):
    """
    Check if path matches pattern.
    
    Pattern matching behaves the same way as it does in Apache Ant.
    That is, it is done per-component. For example the pattern *.h will match 
    file.h but not dir/file.h. Use two asterisks to match any number of components.
    
    Examples:
        lib/*.a will match lib/file.a, but not lib/debug/file.a
        lib/*/* will match lib/a/b, lib/sub1/b.c, etc.
        lib/**/*.a will match lib/file.a, lib/a/file.a, lib/a/b/file.a, etc.
        **/test/** will match test, a/test, test/a, a/b/c/test/d/e, etc.
        dir/file_???.txt will match dir/file_abc.txt, but not dir/file_abcd.txt
        
    fnmatch.fnmatch() is used for the actual matching, so character ranges can also be used.
    """
    path_segments = separate_path(path)
    pattern_segments = separate_path(pattern)
    path_length = len(path_segments)
    pattern_length = len(pattern_segments)

    i = 0
    j = 0
    while i < pattern_length and j < path_length:
        if pattern_segments[i] == "**":
            if i + 1 < pattern_length:
                i += 1
            else:
                #the '**' is at the end, so any path segments after will be matched
                return True
                
            #increment j until a path segment matches or we come to the end
            while j < path_length:
                #in case there are multiple path segments that would match,
                #make sure we find a match with the correct number of segments remaining
                equal_remaining = path_length - j == pattern_length - i
                allow_different = pattern_segments[i:].count("**")
                if (fnmatch.fnmatch(path_segments[j], pattern_segments[i]) and
                    (equal_remaining or allow_different)):
                    break
                else:
                    j += 1
        else:
            #normal segment by segment matching
            if not fnmatch.fnmatch(path_segments[j], pattern_segments[i]):
                return False
            i += 1
            j += 1
            
            #handle the special case of '**/x/**' when x is the last path segment.
            #when i points to the last '**', j will already be one past the end, 
            #so simply increment i again  
            if i == pattern_length - 1 and pattern_segments[i] == "**":
                if j == path_length:
                    i += 1

    #if we have reached here, it should mean that we have successfully 
    #matched all segments
    if i == pattern_length and j == path_length:
        return True

    return False

def match_list(path, patterns):
    """Check if path matches any pattern in a list"""
    for p in patterns:
        if match(path, p):
            return True
    return False
    
def walk(path, depth_limit=None):
    """Walk directory tree rooted at path
    
    For each directory, it yields (dirpath, dirnames, filenames).
    dirpath is the path of the directory being visited, dirnames is the list 
    of directories in dirpath and filenames is the list of files in dirpath. 

    If depth_limit is not None, the tree is only walked up to depth depth_limit. 
    For example, if depth_limit is 2, the contents of the root directory is returned, 
    and then the contents of the subdirectories of the root directory.
    """
    def _walk_recursive(path, depth):
        if depth_limit is None or depth < depth_limit:
            try:
                contents = os.listdir(path)
            except OSError:
                return
                
            dirs = []
            files = []
            for name in contents:
                subpath = os.path.join(path, name)
                if os.path.isdir(subpath):
                    dirs.append(name)
                else:
                    files.append(name)
                
            yield path, dirs, files

            for name in dirs:
                for x in _walk_recursive(os.path.join(path, name), depth + 1):
                    yield x

    for x in _walk_recursive(path, 0):
        yield x

def glob(pattern):
    """Return a generator that yields paths matching pattern
    
    The matching is done with match(), so glob('src/**/*.h') will return 
    all .h files in the directory tree 'src'
    """
    if os.path.exists(pattern):
        yield pattern
    else:
        path = pattern
        depth_limit = 0
        while has_magic(path):
            path, basename = os.path.split(path)
            depth_limit += 1
        if not path:
            path = "."
        if pattern.count("**"):
            depth_limit = None

        for parent, dirs, files in walk(path, depth_limit):
            for p in dirs + files:
                subpath = os.path.join(parent, p)
                if match(subpath, pattern):
                    yield subpath
