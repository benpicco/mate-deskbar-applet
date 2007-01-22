import gnomevfs
import urllib
import shutil
import bz2
import gzip
import tarfile
import threading
import zipfile
from os.path import join, exists
from os import unlink

import deskbar

class FormatNotSupportedError(Exception):
    """
    Raised if the MIME type isn't supported
    """
    pass

class DecompressError(Exception):
    """
    Raised on an error during extraction
    """
    pass

class IExtracter(object):
    """
    Interface for a Extracter
    
    We use the Strategy pattern here
    """
    def extract(archive, destination):
        raise NotImplementedError
    extract = staticmethod(extract)
        
class Bzip2Extracter(IExtracter):
    def extract(archive, destination):
        bz2file = bz2.BZ2File(archive, 'r')
        TarExtracter.extract(bz2file, destination)
        bz2file.close()
    extract = staticmethod(extract)
    
class GzipExtracter(IExtracter):
    def extract(archive, destination):
        gzfile = gzip.GzipFile(archive, 'r')
        TarExtracter.extract(gzfile, destination)
        gzfile.close()
    extract = staticmethod(extract)

class TarExtracter(IExtracter):
    def extract(tar_fileobj, destination):
        if isinstance(tar_fileobj, str):
            tar_fileobj = file(tar_fileobj, 'r')
        tararchive = tarfile.TarFile(fileobj=tar_fileobj)
        for member in tararchive.getmembers():
            tararchive.extract(member, destination)
        tararchive.close()
    extract = staticmethod(extract)
    
class ZipExtracter(IExtracter):
    def extract(archive, destination):
        archive = zipfile.ZipFile(archive, 'r')
        for name in archive.namelist():
            outpath = join(destination, name)
            outfile = file(outpath, 'w')
            outfile.write(archive.read(name))
            outfile.close()
        archive.close()
    extract = staticmethod(extract)
    
class Decompresser(threading.Thread):
    
    def __init__(self, parent, path, dest_dir):
        """
        @type parent: Thread that called Decompresser
        @param path: path pointing to archive
        @param dest_dir: Folder to extract contents to        
        """
        threading.Thread.__init__(self)
        
        self.parent = parent
        self.path = path
        self.dest_dir = dest_dir
    
    def run(self):
        """
        Extract the contents of the file to C{self.dest_dir}
        @raise FormatNotSupportedError:
        """
        mime_type = gnomevfs.get_mime_type(self.path)
        if mime_type == 'application/x-bzip-compressed-tar':
            extracter = Bzip2Extracter
        elif mime_type == 'application/x-compressed-tar':
            extracter = GzipExtracter
        elif mime_type == 'application/zip':
            extracter = ZipExtracter
        elif mime_type == 'application/x-tar':
            extracter = TarExtracter
        elif mime_type == 'text/x-python':
            self.parent.delete_original = False
            return
        else:
            self.parent.install_successful = False
            return
        try:
            extracter.extract(self.path, self.dest_dir)
        except Exception, err:
            self.parent.install_successful = False


class ModuleInstaller:
    
    def __init__(self, module_loader):        
        self.module_loader = module_loader
        self.delete_original = True
        self.local_path = None
        self.install_successful = True
        
    def cleanup(self):
        """
        Delete downloaded data
        """
        if (self.delete_original and exists(self.local_path)):
            unlink(self.local_path)
        
    def install(self, uri_string):       
        """
        Install handler
        
        Basically copys the handlers into the user's handler dir
        and L{deskbar.Watcher} does the rest.
        
        The following MIME types are supported:
            * application/x-bzip-compressed-tar
            * application/x-compressed-tar
            * application/x-tar
            * application/zip
            * text/x-python
        
        @param uri_string: URI of file that should be installed
        @type uri_string: str
        """
        do_cleanup = False
        
        uri = gnomevfs.URI(uri_string)
        if (uri.is_local == 1):
            handlers_path = join(deskbar.USER_HANDLERS_DIR[0], uri.short_name)
            self.local_path = uri.path
            if handlers_path == join(deskbar.USER_HANDLERS_DIR[0], self.local_path):
            	# Source and destination are the same, nothing to do here
            	return self.install_successful
            if (gnomevfs.get_mime_type(uri_string) == "text/x-python"):
                shutil.copy(self.local_path, deskbar.USER_HANDLERS_DIR[0])
                return self.install_successful
        else:
            handlers_path = join(deskbar.USER_HANDLERS_DIR[0], uri.short_name)
            urllib.urlretrieve(uri_string, handlers_path)
            self.local_path = handlers_path
            do_cleanup = True

        decompresser = Decompresser(self, self.local_path, deskbar.USER_HANDLERS_DIR[0])
        decompresser.start()
        # Wait for Decompresser to finish
        decompresser.join()
        
        if do_cleanup:
            self.cleanup()
            
        return self.install_successful
