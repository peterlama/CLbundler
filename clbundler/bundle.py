import os
import shutil
import sqlite3

import fileutils
import exceptions
   
class Package:
    def __init__(self, name, version, deps, files_rel=[], files_dbg=[], files_dev=[]):
        self.name = name
        self.version = version
        self.deps = deps
        self.files["rel"] = files_rel
        self.files["dbg"] = files_dbg
        self.files["dev"] = files_dev

class LibBundle:
    def __init__(self):
        self.is_setup = False
        self.path = None
        self.platform = None
        self.toolchain = None
        self.arch = None

        self._manifest_path = None
    
    def load(self, path):
        self.path = path
        self._manifest_path = os.path.join(path, "MANIFEST.db")
        
        self._verify()
        
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()
        r = cursor.execute("SELECT platform, toolchain, arch FROM info").fetchone()
        
        self.patform = r[0]
        self.toolchain = r[1]
        self.arch = r[2]
        self.is_setup = True
        
        connection.close()
            
            
    def create(self, path, platform, toolchain, arch):
        self.path = path
        
        if os.path.exists(self.path):
            raise ValueError("Directory already exsits: " + self.path)

        self.platform = platform
        self.toolchain = toolchain
        self.arch = arch
        self._manifest_path = os.path.join(self.path, "MANIFEST.db")
        
        os.mkdir(self.path)
        
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()

        cursor.execute("CREATE TABLE installed"
                       "(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "name TEXT UNIQUE, version TEXT)")
        cursor.execute("CREATE TABLE files (id INT, name TEXT, category TEXT)")
        cursor.execute("CREATE TABLE dep_graph (name TEXT, deps TEXT)")

        cursor.execute("CREATE TABLE info (platform TEXT, toolchain TEXT, arch TEXT)")
        cursor.execute("INSERT INTO info VALUES (?,?,?)", (platform, toolchain, arch))

        connection.commit()
        connection.close()
        
        self.is_setup = True
    
    def is_installed(self, package_name):
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()

        row = cursor.execute("SELECT * FROM installed WHERE name = ?",
                             (package_name,)).fetchone()
        connection.commit()
        connection.close()

        return row != None
        
    def install(self, name, version, deps, fileset, force=False):
        if not self.is_setup:
            raise exceptions.BundleError("Instance of LibBundle not associated with any bundle on disk")
        
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()
            
        if force and self.is_installed(name):
            #first remove entries from the database to avoid duplication
            query = "SELECT id FROM installed WHERE name = ?"
            lib_id = cursor.execute(query, (name,)).fetchone()[0]

            cursor.execute("DELETE FROM files WHERE id = ?", (lib_id,))
            cursor.execute("DELETE FROM installed WHERE id = ?", (lib_id,))
            cursor.execute("DELETE FROM dep_graph WHERE name = ?", (name,))
            
        if force or not self.is_installed(name):
            files = {"rel":[], "dbg":[], "dev":[]}
            
            for category in fileset.categories:
                for copy, exclude, dest in fileset.iter_items(category):
                    files[category].extend(self._copy_into_bundle(copy, dest, exclude))
                
            query = "INSERT INTO installed (name, version) VALUES (?,?)"
            cursor.execute(query, (name, version))
            
            query = "SELECT id FROM installed WHERE name = ?"
            lib_id = cursor.execute(query, (name,)).fetchone()[0]
            
            query = "INSERT INTO files VALUES (?,?,?)"
            
            for category in files.keys():
                for filename in files[category]:
                    cursor.execute(query, (lib_id, filename, category))

            for dep_name in deps:
                cursor.execute("INSERT INTO dep_graph VALUES (?,?)", (name, dep_name))
                
        connection.commit()
        connection.close()
        
    def uninstall(self, package_name):
        if not self.is_installed(package_name):
            raise exceptions.BundleError(package_name + " is not installed")
        
        files_delete = self.list_files(package_name)
        
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()
        
        query = "SELECT id FROM installed WHERE name = ?"
        lib_id = cursor.execute(query, (package_name,)).fetchone()[0]

        cursor.execute("DELETE FROM files WHERE id = ?", (lib_id,))
        cursor.execute("DELETE FROM installed WHERE id = ?", (lib_id,))
        cursor.execute("DELETE FROM dep_graph WHERE name = ?", (package_name,))
        
        connection.commit()
        connection.close()
                
        for item in files_delete:
            fileutils.remove(os.path.join(self.path, item[0]))
    
    def installed(self):
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()
         
        result = [row[0] for row in cursor.execute("SELECT name FROM installed")]
         
        connection.close()
            
        return result
    
    def deps(self, package_name):
        if not self.is_installed(package_name):
            raise exceptions.BundleError(package_name + " is not installed")
            
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()
        
        query = "SELECT deps FROM dep_graph WHERE name = ?"
        result = [row[0] for row in cursor.execute(query, (package_name,))]
        
        connection.close()
        
        return result
        
    def list_files(self, package_name, category=""):
        if not self.is_installed(package_name):
            raise exceptions.BundleError(package_name + " is not installed")
            
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()
        
        query = "SELECT id FROM installed WHERE name = ?"
        lib_id = cursor.execute(query, (package_name,)).fetchone()[0]
        
        if category:
            query = "SELECT name FROM files WHERE id = ? AND category = ?"
            files = cursor.execute(query, (lib_id, category)).fetchall()
        else:
            query = "SELECT name FROM files WHERE id = ?"
            files = cursor.execute(query, (lib_id,)).fetchall()
        
        connection.close()
        
        return files
    
    def list_missing_files(self):
        pass

    def list_untracked_files(self):
        pass
        
    def delete_files(self, package_name, files):
        pass

    def _copy_into_bundle(self, patterns, dest_dir, exclude_patterns=[]):
        """copy files and directories described by patterns to dest_dir
        
        dest_dir is assumed to be relative to the bundle path
        """
        dest_dir = os.path.normpath(dest_dir).lstrip("/").lstrip("\\")
        abs_dest_dir = os.path.join(self.path, dest_dir)

        copied = set()
        
        for pattern in patterns:
            for path in fileutils.glob(pattern):
                if not fileutils.match_list(path, exclude_patterns):
                    if not pattern.count("**"):
                        basename = os.path.basename(path)
                        fileutils.copy(path, os.path.join(abs_dest_dir, basename), parents=True, 
                                       replace=True, ignore=fileutils.copy_ignore(exclude_patterns))
                        copied.add(os.path.join(dest_dir, basename))
                    else:
                        #strip the fixed portion of the path
                        #we only want to keep the directory structure after the glob expression
                        pattern_segments = fileutils.separate_path(pattern)
                        path_segments = fileutils.separate_path(path)
                        new_root_i = pattern_segments.index("**")
                        dest = os.path.join(abs_dest_dir, *path_segments[new_root_i:])

                        fileutils.copy(path, dest, parents=True, replace=True, 
                                       ignore=fileutils.copy_ignore(exclude_patterns))

                        #to save memory, only the first level after root is added to 'copied'
                        copied.add(os.path.join(dest_dir, *path_segments[new_root_i:new_root_i+1]))

        return copied

    def _verify(self):
        if not os.path.exists(self._manifest_path):
            raise exceptions.BundleError("Not a valid bundle: missing database")
        
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()
        
        tables = {"dep_graph":["name", "deps"],
                  "files":["id", "name", "category"],
                  "info":["platform", "toolchain", "arch"],
                  "installed":["id", "name", "version"]}
        for table, columns in tables.iteritems():
            try:
                for cn in columns:
                    cursor.execute("SELECT {0} FROM {1}".format(cn, table))
            except sqlite3.OperationalError:
                connection.close()
                raise exceptions.BundleError("Not a valid bundle: database layout is incorrect")
        
        connection.close()
