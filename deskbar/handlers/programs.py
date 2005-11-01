import os, ConfigParser, cgi, re
import glob
from os.path import join, isfile, abspath, splitext, expanduser, exists
from gettext import gettext as _

import gobject
import gtk
import deskbar, deskbar.indexer, deskbar.locale_utils, deskbar.handler_utils
import deskbar.handler
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
	def __init__(self, backend, name, program, icon=None, use_arg=False):
		deskbar.handler.Match.__init__(self, backend, name, icon)
		
		# Strip the %U or %Whatever that have to be parameters
		self._program = re.sub("%\w+", "", program).strip()
		self._use_arg = use_arg
		
	def action(self, text=None):
		self._priority = self._priority+1
		
		# The real program name
		prog = self._program.split(" ", 1)[0]
		
		# The arguments found in the .desktop file
		args = self._program.split(" ")[0:]
		
		if self._use_arg and text != None:
			args.append(text)
			
		print 'Running "%s" "%r"' % (prog, args)
		gobject.spawn_async(args, flags=gobject.SPAWN_SEARCH_PATH)
	
	def get_verb(self):
		return _("Launch <b>%(name)s</b> (%(prog)s)")
		
	def get_name(self, text=None):
		return {
			"name": cgi.escape(self._name),
			"prog": self._program,
		}
		
class GnomeDictMatch(GenericProgramMatch):
	def __init__(self, backend, name, program, icon=None):
		GenericProgramMatch.__init__(self, backend, name, program, icon, True)
	
	def get_verb(self):
		return _("Lookup <b>%(text)s</b> in dictionary")

class GnomeSearchMatch(GenericProgramMatch):
	def __init__(self, backend, name, program, icon=None):
		program = program + " --start --path %s --named" % expanduser("~")
		GenericProgramMatch.__init__(self, backend, name, program, icon, True)
	
	def get_verb(self):
		return _("Search for file names like <b>%(text)s</b>")

class SpecialProgramHandler(deskbar.handler.Handler):
	def __init__(self, desktop, icon="generic.png"):
		deskbar.handler.Handler.__init__(self, icon)
		self._desktop = desktop
		self._match = None
		
	def initialize(self):
		result = parse_desktop_filename(self._desktop)
		if result != None:
			self._match = self.create_match(result["name"], result["program"], result["pixbuf"])
	
	def create_match(self, name, program, icon):
		raise NotImplementedError
		
	def query(self, qstring, qmax=5):
		if self._match != None:
			return [self._match]
		else:
			return []
		
class GnomeDictHandler(SpecialProgramHandler):
	def __init__(self):
		SpecialProgramHandler.__init__(self, "gnome-dictionary.desktop", "gdict")
	
	def create_match(self, name, program, icon):
		return GnomeDictMatch(self, name, program, icon)

class GnomeSearchHandler(SpecialProgramHandler):
	def __init__(self):
		SpecialProgramHandler.__init__(self, "gnome-search-tool.desktop", "gnome-searchtool")
	
	def create_match(self, name, program, icon):
		return GnomeSearchMatch(self, name, program, icon)
		
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
					match = GenericProgramMatch(self, result["name"], result["program"], result["pixbuf"])
					self._indexer.add("%s %s %s %s %s" % (result["name"], result["program"], result["comment"], result["engname"], result["engcomment"]), match)

def parse_desktop_filename(desktop):
	for dir in get_xdg_data_dirs():
		f = join(dir, "applications", desktop)
		if exists(f):
			return parse_desktop_file(f)
	
	return None
	
def parse_desktop_file(desktop):
	try:
		config = ConfigParser.SafeConfigParser({
			"Comment" : "",
			"Icon": "",
			"NoDisplay": "false",
			"Terminal" : "no",
		})
		config.read(desktop)
		if config.getboolean("Desktop Entry", "Terminal"):
			return None
		if config.getboolean("Desktop Entry", "NoDisplay"):
			return None
		
		program = config.get("Desktop Entry", "Exec", True)
		
		name = get_entry_locale(config, "Name")
		comment = get_entry_locale(config, "Comment")

		pixbuf = deskbar.handler_utils.load_icon(config.get("Desktop Entry", "Icon", True))
		
		#FIXME: We will also index in english, see if this is good, or not
		engname = config.get("Desktop Entry", "Name", True)
		engcomment = config.get("Desktop Entry", "Comment", True)
		
		return {
			"program":    program,
			"name":       name,
			"comment":    comment,
			"pixbuf":     pixbuf,
			"engname":    engname,
			"engcomment": engcomment,
		}
		
	except Exception, msg:
		print 'Error:_scan_desktop_files:File Error:%s:%s' % (desktop, msg)
		return None
		
LANGS = deskbar.locale_utils.get_languages()
def get_entry_locale(config, key):
	for lang in LANGS:
		locale_key = "%s[%s]" % (key, lang)
		try:
			return config.get("Desktop Entry", locale_key, True)
		except:
			pass
	
	return config.get("Desktop Entry", key, True)
