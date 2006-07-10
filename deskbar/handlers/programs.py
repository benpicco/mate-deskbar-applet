import os, ConfigParser, cgi, re
import glob
from os.path import join, isfile, abspath, splitext, expanduser, exists, isdir
from gettext import gettext as _
from deskbar.defs import VERSION
import gobject
import gtk
import deskbar, deskbar.Indexer, deskbar.Utils
import deskbar.Handler, deskbar.Match, deskbar.gnomedesktop
from deskbar.Utils import get_xdg_data_dirs

HANDLERS = {
	"ProgramsHandler" : {
		"name": _("Programs"),
		"description": _("Launch a program by its name and/or description"),
		"version": VERSION,
	},
	"GnomeDictHandler" : {
		"name": _("Dictionary"),
		"description": _("Look up word definitions in the dictionary"),
		"version": VERSION,
	},
	"GnomeSearchHandler" : {
		"name": _("Files and Folders Search"),
		"description": _("Find files and folders by searching for a name pattern"),
		"version": VERSION,
	},
	"DevhelpHandler" : {
		"name": _("Developer Documentation"),
		"description": _("Search Devhelp for a function name"),
		"version": VERSION,
	},
}

EXACT_MATCH_PRIO = 100
EXACT_WORD_PRIO = 50

class GenericProgramMatch(deskbar.Match.Match):
	def __init__(self, backend, use_arg=False, desktop=None, desktop_file=None, EXACT_WORD_PRIO, **args):
		deskbar.Match.Match.__init__(self, backend, **args)
		
		self.desktop_file = desktop_file
		self.use_arg = use_arg
		
		self._priority = EXACT_WORD_PRIO
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
			self._match._priority = get_priority_for_name(qstring, self._match._desktop.get_string("Exec"))
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

class PathProgramMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, use_terminal=False, priority=0, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		self.use_terminal = use_terminal
		self._priority = EXACT_MATCH_PRIO
		
	def set_with_terminal(self, terminal):
		self.use_terminal = terminal
		
	def get_hash(self, text=None):
		if not self.use_terminal:
			return text
		else:
			return (text, True)
		
	def action(self, text=None):
		if self.use_terminal:
			try:
				prog = subprocess.Popen(
					text.split(" "),
					stdout=subprocess.PIPE,
					stderr=subprocess.STDOUT)
				
				zenity = subprocess.Popen(
					["zenity", "--title="+text,
						"--window-icon="+join(deskbar.ART_DATA_DIR, "generic.png"),
						"--width=700",
						"--height=500",
						"--text-info"],
					stdin=prog.stdout)
	
				# Reap the processes when they have done
				gobject.child_watch_add(zenity.pid, lambda pid, code: None)
				gobject.child_watch_add(prog.pid, lambda pid, code: None)
				return
			except:
				#No zenity, get out of the if, and launch without GUI
				pass
		
		gobject.spawn_async(text.split(" "), flags=gobject.SPAWN_SEARCH_PATH)			

	def get_category(self):
		return "actions"
	
	def get_verb(self):
		return _("Execute %s") % "<b>%(text)s</b>"
		
class ProgramsHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, gtk.STOCK_EXECUTE)
		self._indexer = deskbar.Indexer.Indexer()
		
	def initialize(self):
		self._scan_desktop_files()
		self._path = [path for path in os.getenv("PATH").split(os.path.pathsep) if path.strip() != "" and exists(path) and isdir(path)]
		
	def query(self, query):
		result = self.query_path_programs(query)
		result += self.query_desktop_programs(query)
		return result
		
	def query_path_programs(self, query):
		args = query.split(" ")
		match = self._check_program(args[0])

		if match != None:
			return [match]
		else:
			return []
	
	def query_desktop_programs(self, query)
		result = []
		for match in self._indexer.look_up(query):
			match._priority = get_priority_for_name(query, match._desktop.get_string("Exec"))
			result.append(match)
		return result
			
	
	def on_key_press(self, query, shortcut):
		if shortcut == gtk.keysyms.t:
			match = self._check_program(query.split(" ")[0])
			if match != None:
				match.set_with_terminal(True)
				return match
			
		return None
		
	def _check_program(self, program):
		for path in self._path:
			prog_path = join(path, program)
			if exists(prog_path) and isfile(prog_path):
				return PathProgramMatch(self, program)	
				
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

def get_priority_for_name(query, name):
	if name.split(" ")[0].endswith(query):
		return EXACT_MATCH_PRIO
	else:
		return EXACT_WORD_PRIO
		
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
