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
}

class GenericProgramMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, icon=None, use_arg=False, desktop=None, desktop_file=None):
		deskbar.Match.Match.__init__(self, backend, name, icon)
		
		self.desktop_file = desktop_file
		self.use_arg = use_arg
		
		self._icon = deskbar.Utils.load_icon_for_desktop_icon(icon)
		self._desktop = desktop
		if desktop == None:
			self._desktop = deskbar.gnomedesktop.item_new_from_file(desktop_file, deskbar.gnomedesktop.LOAD_ONLY_IF_EXISTS)
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
		return "programs"
	
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
	def __init__(self, backend, name, icon, desktop, desktop_file):
		GenericProgramMatch.__init__(self, backend, name, icon, True, desktop, desktop_file)
	
	def get_verb(self):
		return _("Lookup %s in dictionary") % "<b>%(text)s</b>"

class GnomeSearchMatch(GenericProgramMatch):
	def __init__(self, backend, name, icon, desktop, desktop_file):
		GenericProgramMatch.__init__(self, backend, name, icon, True, desktop, desktop_file)
		self._args = ["--start", "--path", expanduser("~"), "--named"]
		
	def get_verb(self):
		return _("Search for file names like %s") % "<b>%(text)s</b>"

class SpecialProgramHandler(deskbar.Handler.Handler):
	def __init__(self, desktop, icon="generic.png"):
		deskbar.Handler.Handler.__init__(self, icon)
		self._desktop = desktop
		self._match = None
		
	def initialize(self):
		result = parse_desktop_filename(self._desktop, False)
		if result != None:
			self._match = self.create_match(result, self._desktop)
	
	def create_match(self, desktop, f):
		raise NotImplementedError
		
	def query(self, qstring, qmax):
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
					cgi.escape(desktop.get_localestring(deskbar.gnomedesktop.KEY_NAME)),
					desktop.get_string(deskbar.gnomedesktop.KEY_ICON),
					desktop=desktop,
					desktop_file=f)

class GnomeSearchHandler(SpecialProgramHandler):
	def __init__(self):
		SpecialProgramHandler.__init__(self, "gnome-search-tool.desktop", "gnome-searchtool")
	
	def create_match(self, desktop, f):
		return GnomeSearchMatch(
					self,
					cgi.escape(desktop.get_localestring(deskbar.gnomedesktop.KEY_NAME)),
					desktop.get_string(deskbar.gnomedesktop.KEY_ICON),
					desktop=desktop,
					desktop_file=f)
		
class ProgramsHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "generic.png")
		self._indexer = deskbar.Indexer.Indexer()
		
	def initialize(self):
		self._scan_desktop_files()
		
	def query(self, query, max):
		return self._indexer.look_up(query)[:max]
		
	def _scan_desktop_files(self):
		for dir in get_xdg_data_dirs():
			for f in glob.glob(join(dir, "applications", "*.desktop")):
				result = parse_desktop_file(f)
				if result != None:
					match = GenericProgramMatch(
								self,
								cgi.escape(result.get_localestring(deskbar.gnomedesktop.KEY_NAME)),
								result.get_string(deskbar.gnomedesktop.KEY_ICON),
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
	for dir in get_xdg_data_dirs():
		f = join(dir, "applications", desktop)
		if exists(f):
			return parse_desktop_file(f, only_if_visible)
	
	return None


def parse_desktop_file(desktop, only_if_visible=True):
	desktop = deskbar.gnomedesktop.item_new_from_file(desktop, deskbar.gnomedesktop.LOAD_ONLY_IF_EXISTS)
	if desktop == None or desktop.get_entry_type() != deskbar.gnomedesktop.TYPE_APPLICATION:
		return None
	if desktop.get_boolean(deskbar.gnomedesktop.KEY_TERMINAL):
		return None
	if only_if_visible and desktop.get_boolean(deskbar.gnomedesktop.KEY_NO_DISPLAY):
		return None
		
	return desktop
