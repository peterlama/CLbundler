import os
import urllib
import logging
import shutil
import sys
import time

import config
import exceptions
import system

class AbstractSourceDownloader(object):
    def __init__(self, name, version, source_info):
        self.source_info = source_info
        self.cache_dir = config.global_config().src_cache_dir()
        self.build_dir = config.global_config().build_dir()
        self.dest_dir = os.path.join(self.build_dir, "{0}-{1}".format(name, version))
        
        self.url = source_info["url"]
        
    def fetch(self):
        pass
    
    def stage(self):
        pass
        
    def _src_needs_update(self, dir1, dir2):
        new_dir = False;
        if not os.listdir(dir1):
            new_dir = True;
        
        if not new_dir and os.path.getmtime(dir1) < os.path.getmtime(dir2):
            return True
        elif new_dir:
            return True
        
        return False

class ArchiveSourceDownloader(AbstractSourceDownloader):
    def __init__(self, name, version, source_info):
        super(ArchiveSourceDownloader, self).__init__(name, version, source_info)
        
        filename = os.path.basename(self.url)
        self.filepath = os.path.join(self.cache_dir, filename)

    def _check_archive_url(self, url):
        try:
            response = urllib.urlopen(url)
        except IOError:
            raise exceptions.InvalidUrlError("Invalid URL: " + url)
            
        if not response.info().gettype().startswith("application"):
            raise exceptions.InvalidUrlError(url + " does not seem to point to a archive file")
             
    def _download_progress(self, blocks, block_size, file_size):
        percent = min(blocks*block_size*100.0 / file_size, 100)
        sys.stdout.write("{0:3.1f}%\r".format(percent))
        sys.stdout.flush()
        
    def fetch(self):
        self._check_archive_url(self.url)
        
        if not os.path.exists(self.filepath):
            logging.getLogger().info("Downloading {0}...".format(os.path.basename(self.filepath)))
            urllib.urlretrieve(self.url, self.filepath, self._download_progress)
        
    def stage(self):
        if not os.path.exists(self.dest_dir):
            tmp_dir = os.path.join(self.cache_dir, "tmp")
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            try:
                os.mkdir(tmp_dir)
            except OSError:
                #On Windows, it is sometimes necessary to wait a little after deleting a 
                #directory before creating it again
                time.sleep(0.01)
                os.mkdir(tmp_dir)
                
            #extract to a temporary directory so that we can get the dir name
            logging.getLogger().info("Extracting {0}...".format(os.path.basename(self.filepath)))
            system.extract(self.filepath, tmp_dir)
            
            contents = os.listdir(tmp_dir)
            src_dir = None
            for n in contents:
                if os.path.isdir(os.path.join(tmp_dir, n)):
                    src_dir = os.path.join(tmp_dir, n)
            
            if not src_dir:
                raise exceptions.SourceArchiveError("No directory in archive")
                
            os.rename(src_dir, self.dest_dir)
            
            shutil.rmtree(tmp_dir)

class GitSourceDownloader(AbstractSourceDownloader):
    def __init__(self, name, version, source_info):
        super(GitSourceDownloader, self).__init__(name, version, source_info)
        
        self.git_dir = os.path.join(self.cache_dir, os.path.basename(self.url))
        
        self.revision = ""
        if self.source_info.has_key("revision"):
            self.revision = self.source_info["revision"]
        
    def fetch(self):
        if not os.path.exists(os.path.join(self.git_dir, "HEAD")):
            logging.getLogger().info("Cloning {0}...".format(os.path.basename(self.url)))
            system.run_cmd("git", ["clone", "--bare", self.url, self.git_dir])
        else:
            logging.getLogger().info("Updating {0}...".format(os.path.basename(self.git_dir)))
            system.run_cmd("git", ["--git-dir=" + self.git_dir, "fetch"])
        
    def stage(self):
        if not os.path.exists(self.dest_dir):
            os.mkdir(self.dest_dir)
        
        if self._src_needs_update(self.dest_dir, self.git_dir):
            options = ["--git-dir=" + self.git_dir, 
                       "--work-tree=" + self.dest_dir, 
                       "checkout", "-q", "-f"]
            if self.revision:
                options.append(self.revision)
            
            logging.getLogger().info("Checking out {0}...".format(self.revision))
            system.run_cmd("git",  options)

class MercurialSourceDownloader(AbstractSourceDownloader):
    def __init__(self, name, version, source_info):
        super(MercurialSourceDownloader, self).__init__(name, version, source_info)
        
        self.hg_dir = os.path.join(self.cache_dir, os.path.basename(self.url))
        
        self.revision = "tip"
        if self.source_info.has_key("revision"):
            self.revision = self.source_info["revision"]
        
    def fetch(self):
        if not os.path.exists(os.path.join(self.hg_dir, ".hg")):
            logging.getLogger().info("Cloning {0}...".format(os.path.basename(self.url)))
            system.run_cmd("hg", ["clone", "--noupdate", self.url, self.hg_dir])
        else:
            old_cwd = os.getcwd()
            os.chdir(self.hg_dir)
            
            logging.getLogger().info("Updating {0}...".format(os.path.basename(self.hg_dir)))
            system.run_cmd("hg", ["pull"])
            
            os.chdir(old_cwd)
        
    def stage(self):
        if not os.path.exists(self.dest_dir):
            os.mkdir(self.dest_dir)
        
        if self._src_needs_update(self.dest_dir, self.hg_dir):
            old_cwd = os.getcwd()
            os.chdir(self.hg_dir)
            
            logging.getLogger().info("Checking out {0}...".format(self.revision))        
            system.run_cmd("hg",  ["archive", "-S", "-y", "-r", self.revision, "-t", "files", self.dest_dir])
            
            os.chdir(old_cwd)
    
class SubversionSourceDownloader(AbstractSourceDownloader):
    def __init__(self, name, version, source_info):
        super(SubversionSourceDownloader, self).__init__(name, version, source_info)
        
        self.svn_dir = os.path.join(self.cache_dir, "{0}-{1}".format(name, version))
        
        self.revision = ""
        if self.source_info.has_key("revision"):
            self.revision = self.source_info["revision"]
        
    def fetch(self):
        if not os.path.exists(os.path.join(self.svn_dir, ".svn")):
            options = ["checkout", self.url, self.svn_dir]
            if self.revision:
                options.extend(["-r", self.revision])
            
            logging.getLogger().info("Checking out {0}...".format(os.path.basename(self.url)))
            system.run_cmd("svn", options)
        else:
            if not self.revision:
                old_cwd = os.getcwd()
                os.chdir(self.svn_dir)
                
                logging.getLogger().info("Updating {0}...".format(os.path.basename(self.svn_dir)))
                system.run_cmd("svn", ["up"])
                
                os.chdir(old_cwd)
        
    def stage(self):
        if not os.path.exists(self.dest_dir):
            os.mkdir(self.dest_dir)
        
        if self._src_needs_update(self.dest_dir, self.svn_dir):
            logging.getLogger().info("Copying to build directory...")      
            system.run_cmd("svn",  ["export", "--force", self.svn_dir, self.dest_dir])
    
downloaders = {
    "archive":ArchiveSourceDownloader,
    "git":GitSourceDownloader,
    "hg":MercurialSourceDownloader,
    "svn":SubversionSourceDownloader
}
