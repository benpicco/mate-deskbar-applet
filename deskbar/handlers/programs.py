import os, ConfigParser, cgi, re
import glob
from os.path import join, isfile, abspath, splitext, expanduser, exists
from gettext import gettext as _

import gobject
import gtk
import deskbar, deskbar.indexer, deskbar.locale_utils, deskbar.handler_utils
import deskbar.handler, deskbar.gnomedesktop
from deskbar.handler_utils import get_xdg_data_dirs

HANDLERS = {
	"ProgramsHandler" : {
		"name": _("Desktop Programs"),
		"description": _("Index the program names and descriptions."),
	},
	"GnomeDictHandler" : {
		"name": _("Dictionary Lookup"),
		"description": _("Type a word and lookup the definition in the dictionary"),
	},
	"GnomeSearchHandler" : {
		"name": _("File Search"),
		"description": _("Type a filename pattern and find matching files on your disk."),
	},
}

class GenericProgramMatch(deskbar.handler.Match):
	def __init__(self, backend, desktop, use_arg=False):
		self._name = cgi.escape(desktop.get_localestring(deskbar.gnomedesktop.KEY_NAME))
		icon = deskbar.handler_utils.load_icon_for_desktop_icon(desktop.get_string(deskbar.gnomedesktop.KEY_ICON))
		
		deskbar.handler.Match.__init__(self, backend, self._name, icon)
		
		self._desktop = desktop
		self._use_arg = use_arg
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
		self._priority = self._priority+1
				
		if self._use_arg and text != None:
			args = [self._desktop.get_string("Exec")]
			if hasattr(self, "_args"):
				args = args + self._args
			args = args + text.split(" ")
			print args
			gobject.spawn_async(args, flags=gobject.SPAWN_SEARCH_PATH)
			# FIXME: This does not launch the App with passed parameters because they are not files..
			#self._desktop.launch(text.split(" "), deskbar.gnomedesktop.LAUNCH_APPEND_PATHS|deskbar.gnomedesktop.LAUNCH_ONLY_ONE)
		else:
			self._desktop.launch([])
	
	def get_verb(self):
		return _("Launch <b>%(name)s</b> (%(prog)s)")
		
	def get_name(self, text=None):
		return {
			"name": self._name,
			"prog": self._display_prog,
		}
		
class GnomeDictMatch(GenericProgramMatch):
	def __init__(self, backend, desktop):
		GenericProgramMatch.__init__(self, backend, desktop, True)
	
	def get_verb(self):
		return _("Lookup <b>%(text)s</b> in dictionary")

class GnomeSearchMatch(GenericProgramMatch):
	def __init__(self, backend, desktop):
		GenericProgramMatch.__init__(self, backend, desktop, True)
		self._args = ["--start", "--path", expanduser("~"), "--named"]
		
	def get_verb(self):
		return _("Search for file names like <b>%(text)s</b>")

class SpecialProgramHandler(deskbar.handler.Handler):
	def __init__(self, desktop, icon="generic.png"):
		deskbar.handler.Handler.__init__(self, icon)
		self._desktop = desktop
		self._match = None
		
	def initialize(self):
		result = parse_desktop_filename(self._desktop, False)
		if result != None:
			self._match = self.create_match(result)
	
	def create_match(self, desktop):
		raise NotImplementedError
		
	def query(self, qstring, qmax=5):
		if self._match != None:
			return [self._match]
		else:
			return []
		
class GnomeDictHandler(SpecialProgramHandler):
	def __init__(self):
		SpecialProgramHandler.__init__(self, "gnome-dictionary.desktop", "gdict")
	
	def create_match(self, desktop):
		return GnomeDictMatch(self, desktop)

class GnomeSearchHandler(SpecialProgramHandler):
	def __init__(self):
		SpecialProgramHandler.__init__(self, "gnome-search-tool.desktop", "gnome-searchtool")
	
	def create_match(self, desktop):
		return GnomeSearchMatch(self, desktop)
		
class ProgramsHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "generic.png")
		self._indexer = deskbar.indexer.Index()
		
	def initialize(self):
		self._scan_desktop_files()
		
	def query(self, query, max=5):
		return self._indexer.look_up(query)[:max]
		
	def _scan_desktop_files(self):
		for dir in get_xdg_data_dirs():
			for f in glob.glob(join(dir, "applications", "*.desktop")):
				result = parse_desktop_file(f)
				if result != None:
					match = GenericProgramMatch(self, result)
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
