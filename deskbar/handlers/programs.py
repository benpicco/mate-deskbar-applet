import os, ConfigParser, cgi, re
import glob
from os.path import join, isfile, abspath, splitext, expanduser, exists
from gettext import gettext as _

import gobject
import gtk
import deskbar, deskbar.Indexer, deskbar.Utils
import deskbar.Handler, deskbar.gnomedesktop
from deskbar.Utils import get_xdg_data_dirs

HANDLERS = {
	"ProgramsHandler" : {
		"name": _("Programs"),
		"description": _("Launch a program by its name and/or description"),
	},
	"GnomeDictHandler" : {
		"name": _("Dictionary"),
		"description": _("Look up word definitions in the dictionary"),
	},
	"GnomeSearchHandler" : {
		"name": _("Files and Folders Search"),
		"description": _("Find files and folders by searching for a name pattern"),
	},
	"DevhelpHandler" : {
		"name": _("Developer Documentation"),
		"description": _("Search Devhelp for a function name"),
	},
}

class GenericProgramMatch(deskbar.Match.Match):
	def __init__(self, backend, use_arg=False, desktop=None, desktop_file=None, **args):
		deskbar.Match.Match.__init__(self, backend, **args)
		
		self.desktop_file = desktop_file
		self.use_arg = use_arg
		
		self._icon = deskbar.Utils.load_icon_for_desktop_icon(self.icon)
		self._desktop = desktop
		if desktop == None:
			self._desktop = parse_desktop_filename(desktop_file)
			if self._desktop == None:
				raise Exception("Desktop file not found, ignoring")
		
		# Strip %U or whatever arguments in Exec field
		exe = re.sub("%\w+", "", self._desktop.get_string("Exec"))
		# Strip any absolute path like /usr/bin/something to display only something
		i = exe.split(" ")[0].rfind("/")
		if i != -1:
			exe = exe[i+1:]
		
		self._display_prog = cgi.escape(exe).strip()
	
	def get_hash(self, text=None):
		return self._display_prog
		
	def action(self, text=None):
		if self.use_arg and text != None:
			args = [self._desktop.get_string("Exec")]
			if hasattr(self, "_args"):
				args = args + self._args
			args = args + text.split(" ")

			gobject.spawn_async(args, flags=gobject.SPAWN_SEARCH_PATH)
			# FIXME: This does not launch the App with passed parameters because they are not files..
			#self._desktop.launch(text.split(" "), deskbar.gnomedesktop.LAUNCH_APPEND_PATHS|deskbar.gnomedesktop.LAUNCH_ONLY_ONE)
		else:
			self._desktop.launch([])

	def get_category(self):
		return "actions"
	
	def get_verb(self):
		#translators: First %s is the programs full name, second is the executable name
		#translators: For example: Launch Text Editor (gedit)
		return _("Launch <b>%(name)s</b> (%(prog)s)")
		
	def get_name(self, text=None):
		return {
			"name": self.name,
			"prog": self._display_prog,
		}
		
class GnomeDictMatch(GenericProgramMatch):
	def __init__(self, backend, use_arg=True, **args):
		GenericProgramMatch.__init__(self, backend, use_arg=use_arg, **args)
		self._args = ["--look-up"]
	
	def get_verb(self):
		return _("Lookup %s in dictionary") % "<b>%(text)s</b>"

class GnomeSearchMatch(GenericProgramMatch):
	def __init__(self, backend, use_arg=True, **args):
		GenericProgramMatch.__init__(self, backend, use_arg=use_arg, **args)
		self._args = ["--start", "--path", expanduser("~"), "--named"]
		
	def get_verb(self):
		return _("Search for file names like %s") % "<b>%(text)s</b>"

class DevhelpMatch(GenericProgramMatch):
	def __init__(self, backend, use_arg=True, **args):
		GenericProgramMatch.__init__(self, backend, use_arg=use_arg, **args)
		self._args = ["-s"]
		
	def get_verb(self):
		return _("Search in Devhelp for %s") % "<b>%(text)s</b>"

class SpecialProgramHandler(deskbar.Handler.Handler):
	def __init__(self, desktop, icon=gtk.STOCK_EXECUTE):
		deskbar.Handler.Handler.__init__(self, icon)
		self._desktop = desktop
		self._match = None
		
	def initialize(self):
		result = parse_desktop_filename(self._desktop, False)
		if result != None:
			self._match = self.create_match(result, self._desktop)
	
	def create_match(self, desktop, f):
		raise NotImplementedError
		
	def query(self, qstring):
		if self._match != None:
			return [self._match]
		else:
			return []
		
class GnomeDictHandler(SpecialProgramHandler):
	def __init__(self):
		SpecialProgramHandler.__init__(self, "gnome-dictionary.desktop", "gdict")
	
	def create_match(self, desktop, f):
		return GnomeDictMatch(
					self,
					name=cgi.escape(desktop.get_localestring(deskbar.gnomedesktop.KEY_NAME)),
					icon=desktop.get_string(deskbar.gnomedesktop.KEY_ICON),
					desktop=desktop,
					desktop_file=f)

class GnomeSearchHandler(SpecialProgramHandler):
	def __init__(self):
		SpecialProgramHandler.__init__(self, "gnome-search-tool.desktop", "gnome-searchtool")
	
	def create_match(self, desktop, f):
		return GnomeSearchMatch(
					self,
					name=cgi.escape(desktop.get_localestring(deskbar.gnomedesktop.KEY_NAME)),
					icon=desktop.get_string(deskbar.gnomedesktop.KEY_ICON),
					desktop=desktop,
					desktop_file=f)
		
class DevhelpHandler(SpecialProgramHandler):
	def __init__(self):
		SpecialProgramHandler.__init__(self, "devhelp.desktop", "devhelp")
	
	def create_match(self, desktop, f):
		return DevhelpMatch(
					self,
					name=cgi.escape(desktop.get_localestring(deskbar.gnomedesktop.KEY_NAME)),
					icon=desktop.get_string(deskbar.gnomedesktop.KEY_ICON),
					desktop=desktop,
					desktop_file=f)
		
class ProgramsHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, gtk.STOCK_EXECUTE)
		self._indexer = deskbar.Indexer.Indexer()
		
	def initialize(self):
		self._scan_desktop_files()
		
	def query(self, query):
		return self._indexer.look_up(query)[:deskbar.DEFAULT_RESULTS_PER_HANDLER]
		
	def _scan_desktop_files(self):
		for dir in get_xdg_data_dirs():
			for f in glob.glob(join(dir, "applications", "*.desktop")):
				result = parse_desktop_file(f)
				if result != None:
					match = GenericProgramMatch(
								self,
								name=cgi.escape(result.get_localestring(deskbar.gnomedesktop.KEY_NAME)),
								icon=result.get_string(deskbar.gnomedesktop.KEY_ICON),
								desktop=result,
								desktop_file=f)
					self._indexer.add("%s %s %s %s %s" % (
								result.get_string("Exec"),
								result.get_localestring(deskbar.gnomedesktop.KEY_NAME),
								result.get_localestring(deskbar.gnomedesktop.KEY_COMMENT),
								result.get_string(deskbar.gnomedesktop.KEY_NAME),
								result.get_string(deskbar.gnomedesktop.KEY_COMMENT),
							), match)

def parse_desktop_filename(desktop, only_if_visible=True):
	if desktop[0] == "/" and exists(desktop):
		return parse_desktop_file(desktop, only_if_visible)
			
	for dir in get_xdg_data_dirs():
		f = join(dir, "applications", desktop)
		if exists(f):
			return parse_desktop_file(f, only_if_visible)
	
	return None


def parse_desktop_file(desktop, only_if_visible=True):
	try:
		desktop = deskbar.gnomedesktop.item_new_from_file(desktop, deskbar.gnomedesktop.LOAD_ONLY_IF_EXISTS)
	except Exception, e:
		print 'Couldn\'t read desktop file:%s:%s' % (desktop, e)
		return None
	
	if desktop == None or desktop.get_entry_type() != deskbar.gnomedesktop.TYPE_APPLICATION:
		return None
	if desktop.get_boolean(deskbar.gnomedesktop.KEY_TERMINAL):
		return None
	if only_if_visible and desktop.get_boolean(deskbar.gnomedesktop.KEY_NO_DISPLAY):
		return None
		
	return desktop
