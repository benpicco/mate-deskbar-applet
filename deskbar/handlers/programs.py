import os, ConfigParser, cgi, re
from os.path import join, isfile, abspath, splitext
from gettext import gettext as _

import gtk
import deskbar, deskbar.indexer
import handler

PRIORITY = 100
icon_theme = gtk.icon_theme_get_default()

class ProgramsMatch(handler.Match):
	def __init__(self, backend, name, program, icon=None):
		handler.Match.__init__(self, backend, name, icon)
		
		# Strip the %U or %Whatever that have to be parameters
		self._program = re.sub("%\w+", "", program)
		
	def action(self, text=None):
		self._priority = self._priority+1
		os.spawnlp(os.P_NOWAIT, self._program, self._program)
	
	def get_verb(self):
		return _("Launch <b>%(name)s</b> (%(prog)s)")
		
	def get_name(self):
		return {
			"name": cgi.escape(self._name),
			"prog": self._program.split(" ", 1)[0]
		}
		
class PathProgramMatch(handler.Match):
	def __init__(self, backend, name):
		handler.Match.__init__(self, backend, name)
		
	def action(self, text=None):
		self._priority = self._priority+1
		if text == None:
			os.spawnlp(os.P_NOWAIT, self._name, self._name)
		else:
			args = text.split(" ")
			os.spawnlp(os.P_NOWAIT, self._name, self._name, args[1:])
	
	def get_verb(self):
		return _("Execute <b>%(text)s</b>")

class PathProgramsHandler(handler.Handler):
	def __init__(self):
		handler.Handler.__init__(self, "generic.png")
		
		self._programs = {}
		print 'Starting PATH programs indexation'
		self._scan_path()
		print '\tDone !'
	
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		query = query.split(" ", 1)[0]
		if query in self._programs:
			return [self._programs[query]]
		else:
			return []
			
	def _scan_path(self):
		for path in os.getenv("PATH").split(os.path.pathsep):
			for program in [f for f in os.listdir(path) if isfile(join(path, f))]:
				self._programs[program] = PathProgramMatch(self, program)
		
class ProgramsHandler(handler.Handler):
	def __init__(self):
		handler.Handler.__init__(self, "generic.png")
		
		self._indexer = deskbar.indexer.Index()
		print 'Starting .desktop file indexation'
		self._scan_desktop_files()
		print '\tDone !'
		
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		return self._indexer.look_up(query)[:5]
		
	def _scan_desktop_files(self):
		desktop_dir = abspath(join("/", "usr", "share", "applications"))
		icon_dir = abspath(join("/", "usr", "share", "pixmaps"))
		
		files = [join(desktop_dir, name) for name in os.listdir(desktop_dir)]
		for f in files:
			try:
				config = ConfigParser.SafeConfigParser({
					"Comment" : "",
					"Terminal" : "no",
				})
				config.read(f)
				if config.getboolean("Desktop Entry", "Terminal"):
					continue

				name = config.get("Desktop Entry", "Name", True)
				program = config.get("Desktop Entry", "Exec", True)
				comment = config.get("Desktop Entry", "Comment", True)
												
				pixbuf = None
				try:
					icon = config.get("Desktop Entry", "Icon", True)
						
					# FIXME: Maybe we want to do a matching for extension
					if splitext(icon)[1] == "":
						icon = icon+".png"
						
					pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(join(icon_dir, icon), -1, deskbar.ICON_SIZE)
				except Exception, msg1:
					try:
						pixbuf = icon_theme.load_icon(splitext(icon)[0], deskbar.ICON_SIZE, gtk.ICON_LOOKUP_USE_BUILTIN)
					except Exception, msg2:
						print 'Error:_scan_desktop_files:Icon Load Error:%s (%s)' % (msg2, msg1)
				
				match = ProgramsMatch(self, name, program, pixbuf)
				self._indexer.add("%s %s %s" % (name, program, comment), match)
			except Exception, msg:
				print 'Error:_scan_desktop_files:File Error:%s:%s' % (f, msg)
				continue
			
