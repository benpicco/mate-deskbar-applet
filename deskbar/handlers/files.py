from deskbar.core.Watcher import FileWatcher
from deskbar.defs import VERSION
from deskbar.handlers.actions.ActionsFactory import get_actions_for_uri
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.OpenFileAction import OpenFileAction
from deskbar.handlers.actions.OpenWithNautilusAction import OpenWithNautilusAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from os.path import join, basename, normpath, abspath, dirname
from os.path import split, expanduser, exists, isfile
import deskbar, deskbar.core.Indexer
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gio
import gtk
import logging
import os
import urllib

LOGGER = logging.getLogger(__name__)

HANDLERS = ["FileFolderHandler"]

GTK_BOOKMARKS_FILE = expanduser("~/.gtk-bookmarks")

class FileMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, absname=None, **args):
        deskbar.interfaces.Match.__init__(self, name=name, icon=absname, category="files", **args)
        self.absname = absname
        self.add_action( OpenFileAction(name, absname ) )
        self.add_all_actions( get_actions_for_uri(absname) )
    
    def get_hash(self):
        return self.absname

class FolderMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, absname=None, **args):
        deskbar.interfaces.Match.__init__(self, name=name, icon=absname, category="places", **args)
        self.absname = absname
        self.add_action( ShowUrlAction(name, absname) )
        self.add_all_actions( get_actions_for_uri(absname) )
    
    def get_hash(self):
        return self.absname

class GtkBookmarkMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, path=None, **args):
        deskbar.interfaces.Match.__init__(self, icon="gtk-open", name=name, category="places", **args)
        self.path = path
        self.add_action( OpenWithNautilusAction(name, path) )
        self.add_all_actions( get_actions_for_uri(path) )
    
    def get_hash(self):
        return self.path

class VolumeMatch (deskbar.interfaces.Match):
    def __init__(self, name=None, drive=None, icon=None, **args):
        deskbar.interfaces.Match.__init__(self, name=name, category="places", icon=icon, **args)
        self.drive = drive
        self.add_action( OpenWithNautilusAction(name, drive) )
        # FIXME:
        # _("Location") should be _("Location of %s") % name
        self.add_action( CopyToClipboardAction(_("Location"), drive) )

    def get_hash(self):
        return self.drive
        
class FileFolderHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon':  deskbar.core.Utils.load_icon(gtk.STOCK_OPEN),
             "name": _("Files, Folders and Places"),
             "description": _("View your files, folders, bookmarks, drives, network places by name"),
             "version": VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self._locations = {}
        self._volume_monitor = gio.volume_monitor_get()
        
    def initialize(self):
        # Gtk Bookmarks --
        if not hasattr(self, 'watcher'):
            self.watcher = FileWatcher()
            self.watcher.connect('changed', lambda watcher, f: self._scan_bookmarks_files())
        
        self.watcher.add(GTK_BOOKMARKS_FILE)
        self._scan_bookmarks_files()

    def stop(self):
        self.watcher.remove(GTK_BOOKMARKS_FILE)
        
    def query(self, query):
        
        result = []
        result += self._query_filefolder(query, False)
        result += self._query_filefolder(query, True)
        
        # Gtk Bookmarks
        lquery = query.lower()
        for bmk, (name, loc) in self._locations.items():
            if bmk.startswith(lquery):
                gtk_bookmark_match = GtkBookmarkMatch(name, loc, priority=self.get_priority())
                result.append(gtk_bookmark_match)
        
        # Mounts
        for mount in self._volume_monitor.get_mounts():
            if not mount.get_name().lower().startswith(lquery): continue
            
            uri = mount.get_root()
            if uri != None:
                icon = "drive-harddisk"
                vol_match = VolumeMatch (mount.get_name(), uri.get_path(), icon, priority=self.get_priority())
                result.append (vol_match)
        
        self._emit_query_ready(query, result)
    
    def _query_filefolder(self, query, is_file):
        completions, prefix, relative = filesystem_possible_completions(query, is_file)
        if is_file:
            return [FileMatch(join(prefix, basename(completion)), "file://"+completion, priority=self.get_priority()) for completion in completions]
        else:
            return [FolderMatch(join(prefix, basename(completion)), "file://"+completion, priority=self.get_priority()) for completion in completions]
    
    def _scan_bookmarks_files(self):
        if not isfile(GTK_BOOKMARKS_FILE):
            return
            
        for line in file(GTK_BOOKMARKS_FILE):
            line = line.strip()
             # First column is url, second the label
            cols = line.split(" ", 1)
            try:
                uri = urllib.unquote(cols[0])
                
                gfile = gio.File(uri=uri)
                
                # We can only check if file exists for local files
                if gfile.get_uri_scheme() == "file":
                    file_exists = gfile.query_exists()
                else:
                    file_exists = True
                    
                if file_exists:
                    name = gfile.get_basename()
                    
                    if len(cols) > 1:
                        display_name = cols[1]
                    else:
                        display_name = name    
                    
                    self._locations[name.lower()] = (display_name, gfile.get_uri())
                    self._locations[display_name.lower()] = (display_name, gfile.get_uri())
            except Exception, msg:
                LOGGER.exception(msg)
                
def filesystem_possible_completions(prefix, is_file=False):
    """
    Given an path prefix, retrieve the file/folders in it.
    If files is False return only the folder, else return only the files.
    Return a tuple (list, prefix, relative)
      list is a list of files whose name starts with prefix
      prefix is the prefix effectively used, and is always a directory
      relative is a flag indicating whether the given prefix was given without ~ or /
    """
    relative = False
    # Path with no leading ~ or / are considered relative to ~
    if not prefix.startswith("~") and not prefix.startswith("/"):
        relative = True
        prefix = join("~/", prefix)
    # Path starting with ~test are considered in ~/test
    if prefix.startswith("~") and not prefix.startswith("~/") and len(prefix) > 1:
        prefix = join("~/", prefix[1:])
    if prefix.endswith("/"):
        prefix = prefix[:-1]
        
    if prefix == "~":
        return ([expanduser(prefix)], dirname(expanduser(prefix)), relative)

    # Now we see if the typed name matches exactly a file/directory, or
    # If we must take the parent directory and match the beginning of each file
    start = None
    path = normpath(abspath(expanduser(prefix)))        

    prefix, start = split(prefix)
    path = normpath(abspath(expanduser(prefix)))    
    if not exists(path):
        # The parent dir wasn't a valid file, exit
        return ([], prefix, relative)
    
    # Now we list all files contained in path. Depending on the parameter we return all
    # files or all directories only. If there was a "start" we also match each name
    # to that prefix so typing ~/cvs/x will match in fact ~/cvs/x*
    
    # First if we have an exact file match, and we requested file matches we return it alone,
    # else, we return the empty file set
    if my_isfile(path):
        LOGGER.debug("Myisfile: %s", is_file)
        if is_file:
            return ([path], dirname(prefix), relative)
        else:
            return ([], prefix, relative)

    try:
        return ([f
            for f in map(lambda x: join(path, x), os.listdir(path))
            if my_isfile(f) == is_file and not basename(f).startswith(".") and (start == None or basename(f).startswith(start))
        ], prefix, relative)
    except OSError, e:
        LOGGER.exception(e)
        return ([], prefix, relative)

#FIXME: gross hack to detect .savedSearches from nautilus as folders
def my_isfile(path):
    return isfile(path) and not path.endswith(".savedSearch")
