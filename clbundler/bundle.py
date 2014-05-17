import os
import shutil
import sqlite3
    
class Package:
    def __init__(self, name, version, deps, files_rel, files_dbg=[], files_dev=[]):
        self.name = name
        self.version = version
        self.deps = deps
        self.files_rel = files_rel
        self.files_dbg = files_dbg
        self.files_dev = files_dev

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
        if os.path.exists(self._manifest_path):
            #TODO: error handling
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
                             (name,)).fetchone()
        connection.commit()
        connection.close()

        return row != None
        
    def install(self, package):
        if self.is_setup and not self.is_installed(package.name):
            connection = sqlite3.connect(self._manifest_path)
            cursor = connection.cursor()
            
            query = "INSERT INTO installed (name, version) VALUES (?,?)"
            cursor.execute(query, (package.name, package.version))
            
            query = "SELECT id FROM installed WHERE name = ?"
            lib_id = cursor.execute(query, (package.name,)).fetchone()[0]
            
            query = "INSERT INTO files VALUES (?,?,?)"
            #TODO: make sure mutually exclusive
            for name in package.files_rel:
                cursor.execute(query, (lib_id, name, "rel"))
            for name in package.files_dbg:
                cursor.execute(query, (lib_id, name, "dbg"))
            for name in package.files_dev:
                cursor.execute(query, (lib_id, name, "dev"))

            for dep_name in package.deps:
                cursor.execute("INSERT INTO dep_graph VALUES (?,?)", (package.name, dep_name))
                
            connection.commit()
            connection.close()
        
    def uninstall(self, package_name):
        if not self.is_installed(name):
            #raise LibPackError(name + " is not installed")
            return
        
        files_delete = self.list_files(package_name)
        
        connection = sqlite3.connect(self._manifest_path)
        cursor = connection.cursor()
        
        query = "SELECT id FROM installed WHERE name = ?"
        lib_id = cursor.execute(query, (package_name,)).fetchone()[0]

        cursor.execute("DELETE FROM files WHERE id = ?", (lib_id,))
        cursor.execute("DELETE FROM installed WHERE id = ?", (lib_id,))
        
        connection.commit()
        connection.close()
                
        for item in files_delete:
            path = os.path.join(self.path, item[0])
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
    
    def list_installed(self):
        if self.is_setup:
            connection = sqlite3.connect(self._manifest_path)
            cursor = conn.cursor()
            
            query = "SELECT name FROM installed"
            result = cursor.execute(query, (package_name,)).fetchall()
             
            connection.close()
            
            return result
        
    def list_files(self, package_name, category=""):
        if self.is_installed(package_name):
            connection = sqlite3.connect(self._manifest_path)
            cursor = conn.cursor()
            
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
