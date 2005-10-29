import gnomevfs
import gobject, gtk

class Watcher(gobject.GObject):
	__gsignals__ = {
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
	}
	def __init__(self):
		gobject.GObject.__init__(self)
		self.watched = {}
		self.monitor_type = gnomevfs.MONITOR_FILE
		
	def add(self, args):
		if not type(args) is list:
			args = [args]

		for name in args:
			if name == "":
				continue
				
			if not name in self.watched:
				try:
					self.watched[name] = gnomevfs.monitor_add(name, self.monitor_type, self._on_change)
				except Exception, msg:
					print 'Error:add_watched_file:', msg
					self.watched[name] = 0
	
	def remove(self, args):
		if not type(args) is list:
			args = [args]
			
		for name in args:
			if name in self.watched:
				if self.watched[name] != 0:
					gnomevfs.monitor_cancel(self.watched[name])
				del self.watched[name]
	
	def remove_all(self):
		self.remove(self.watched.keys())
				
	def _on_change(self, monitor, changed, event):
		if event == gnomevfs.MONITOR_EVENT_CHANGED or event == gnomevfs.MONITOR_EVENT_CREATED:
			self.emit('changed', gnomevfs.get_local_path_from_uri(changed))

if gtk.gtk_version < (2,8,0):
	gobject.type_register(Watcher)
	
class FileWatcher(Watcher):
	def __init__(self):
		Watcher.__init__(self)

class DirWatcher(Watcher):
	def __init__(self):
		Watcher.__init__(self)
		self.monitor_type = gnomevfs.MONITOR_DIRECTORY
