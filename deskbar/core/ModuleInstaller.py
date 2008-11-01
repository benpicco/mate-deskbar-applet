import gio
import urllib
import shutil
import bz2
import gzip
import tarfile
import threading
import zipfile
from os.path import join, exists
from os import unlink
import logging

import deskbar

LOGGER = logging.getLogger(__name__)

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
        tararchive = tarfile.TarFile("", "r", fileobj=tar_fileobj)
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
        gfile = gio.File(path=self.path)
        try:
            fileinfo = gfile.query_info("standard::content-type")
        except Exception, e:
            self.parent_error = (Exception, e.message)
            return
        
        mime_type = gio.content_type_get_mime_type (fileinfo.get_content_type())
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
            self.parent.error = (FormatNotSupportedError, mime_type+" is not supported")
            return
        
        extracter.extract(self.path, self.dest_dir)


class ModuleInstaller:
    
    def __init__(self, module_loader):        
        self.module_loader = module_loader
        
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
        self._reset()
        
        if (uri_string.startswith("file://")):
            gfile = gio.File(uri=uri_string)
            handlers_path = join(deskbar.USER_HANDLERS_DIR[0], gfile.get_basename())
            self.local_path = gfile.get_path()
            if handlers_path == join(deskbar.USER_HANDLERS_DIR[0], self.local_path):
                # Source and destination are the same, nothing to do here
                return
            
            fileinfo = gfile.query_info ("standard::content-type")
            mime_type = gio.content_type_get_mime_type (fileinfo.get_content_type())
            if (mime_type == "text/x-python"):
                shutil.copy(self.local_path, deskbar.USER_HANDLERS_DIR[0])
                return
        else:
            gfile = gio.File(path=uri_string)
            handlers_path = join(deskbar.USER_HANDLERS_DIR[0], gfile.get_basename())
            urllib.urlretrieve(uri_string, handlers_path)
            self.local_path = handlers_path
            do_cleanup = True

        decompresser = Decompresser(self, self.local_path, deskbar.USER_HANDLERS_DIR[0])
        decompresser.start()
        # Wait for Decompresser to finish
        decompresser.join()
        
        if self.error != None:
            raise self.error[0](self.error[1])
        
        if do_cleanup:
            self.cleanup()
            
    def _reset(self):
        self.error = None
        self.delete_original = True
        self.local_path = None
        
