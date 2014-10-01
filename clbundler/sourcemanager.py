import os
import logging

import config
import system
import exceptions
from downloaders import downloaders
    
def get_source(dest_dir, name, version, source_info):
    """
    
    """
    try:
        downloader = downloaders[source_info["type"]](name, version, source_info)
        downloader.fetch()
        downloader.stage()
        
        return downloader.dest_dir
    except KeyError:
        raise exceptions.SourceError("Unknown downloader type '{0}'".format(source_info["type"]))
    

def patch_source(names, paths, src_dir):
    """Apply patches in src_dir
    
    Arguments:
    names -- list of patch names without extension
    paths -- list of directories to search for patch files
    src_dir -- directory to apply patches in
    """
    patches = []
    for n in names:
        patch = ""
        for p in paths:
            if os.path.exists(os.path.join(p, n + ".diff")):
                patch = os.path.join(p, n + ".diff")
                break          
        if not patch:
            raise exceptions.FileNotFoundError("Could not find patch: {0}.diff in \n{1}".format(n, paths))
            
        patches.append(patch)
        
    system.patch(patches, src_dir)
    
