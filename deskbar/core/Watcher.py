"""
Helper classes to monitor directories/files for changes
"""

import gio
import glib
import gobject
import gtk
import logging
from os.path import isdir

LOGGER = logging.getLogger(__name__)

class Watcher(gobject.GObject):
    __gsignals__ = {
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
    }
    def __init__(self):
        gobject.GObject.__init__(self)
        self.watched = {}
        self._get_monitor_func = "monitor_file"
        
    def add(self, args):
        if not type(args) is list:
            args = [args]

        for name in args:
            if name == "":
                continue
                
            if not name in self.watched:
                gfile = gio.File (path=name)
                
                try:
                    self.watched[name] = getattr(gfile, self._get_monitor_func) ()
                except Exception, msg:
                    LOGGER.exception(msg)
                    self.watched[name] = 0
                    
                self.watched[name].connect ("changed", self._on_changed)
    
    def remove(self, args):
        if not type(args) is list:
            args = [args]
            
        for name in args:
            if name in self.watched:
                if self.watched[name] != 0:
                    self.watched[name].cancel()
                del self.watched[name]
    
    def remove_all(self):
        self.remove(self.watched.keys())
                
    def _on_changed(self, monitor, file, other_file, event_type):
        if event_type == gio.FILE_MONITOR_EVENT_CHANGED \
            or event_type == gio.FILE_MONITOR_EVENT_CREATED:
            glib.idle_add(self.emit, 'changed', file.get_path ())

class FileWatcher(Watcher):
    def __init__(self):
        Watcher.__init__(self)

class DirWatcher(Watcher):
    def __init__(self):
        Watcher.__init__(self)
        self._get_monitor_func = "monitor_directory"

if gtk.pygtk_version < (2,8,0):
    gobject.type_register(Watcher)
    gobject.type_register(FileWatcher)
    gobject.type_register(DirWatcher)
