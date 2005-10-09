import os, ConfigParser, cgi, re
import glob
from os.path import join, isfile, abspath, splitext, expanduser
from gettext import gettext as _

import gtk
import deskbar, deskbar.indexer, deskbar.locale_utils
import deskbar.handler

EXPORTED_CLASS = "ProgramsHandler"
NAME = _("Desktop Programs")

PRIORITY = 100
icon_theme = gtk.icon_theme_get_default()

SPECIAL_PROGRAMS = {
	"gnome-search-tool": (_("Search for file names like <b>%(arg)s</b>"),
						["--start", "--path", expanduser("~"), "--named"]),
	
	"gnome-dictionary": (_("Search <b>%(arg)s</b> in Gnome Dictionary"),
						[]),
	"best":				(_("Search <b>%(arg)s</b> with Beagle"),
						["--show-window"]),
}
	
class ProgramsMatch(deskbar.handler.Match):
	def __init__(self, backend, name, program, icon=None):
		deskbar.handler.Match.__init__(self, backend, name, icon)
		
		# Strip the %U or %Whatever that have to be parameters
		self._program = re.sub("%\w+", "", program)
		
	def action(self, text=None):
		self._priority = self._priority+1
		
		# The real program name
		prog = self._program.split(" ", 1)[0]
		
		# The arguments found in the .desktop file
		args = self._program.split(" ")[0:]
		
		# The special arguments for particular programs
		if prog in SPECIAL_PROGRAMS:
			for arg in SPECIAL_PROGRAMS[prog][1]:
				args.append(arg)
			# Also contract the whole query in one argument
			if text != None:
				terms = text.split(" ", 1)[1:]
				if len(terms) > 0 and terms[0] != "":
					args.append(terms[0])
				
		print 'Running "%s" "%r"' % (prog, args)
		os.spawnvp(os.P_NOWAIT, prog, args)
	
	def get_verb(self):
		prog = self._program.split(" ", 1)[0]
		if prog in SPECIAL_PROGRAMS:
			return SPECIAL_PROGRAMS[prog][0]
		else:
			return _("Launch <b>%(name)s</b> (%(prog)s)")
		
	def get_name(self, text=None):
		args = ""
		if text != None:
			terms = text.split(" ", 1)[1:]
			if len(terms) > 0 and terms[0] != "":
				args = terms[0]
		return {
			"name": cgi.escape(self._name),
			"prog": self._program.split(" ", 1)[0],
			"arg": args,
		}
		
class ProgramsHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "generic.png")
		
		self._indexer = deskbar.indexer.Index()
		print 'Starting .desktop file indexation'
		self._scan_desktop_files()
		print '\tDone !'
		
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		#query = query.split(" ", 1)[0]
		return self._indexer.look_up(query)[:5]
		
	def _scan_desktop_files(self):
		desktop_dir = abspath(join("/", "usr", "share", "applications"))
		icon_dir = abspath(join("/", "usr", "share", "pixmaps"))
		
		for f in glob.glob(desktop_dir + '/*.desktop'):
			try:
				config = ConfigParser.SafeConfigParser({
					"Comment" : "",
					"Terminal" : "no",
				})
				config.read(f)
				if config.getboolean("Desktop Entry", "Terminal"):
					continue

				program = config.get("Desktop Entry", "Exec", True)
				
				name = get_entry_locale(config, "Name")
				comment = get_entry_locale(config, "Comment")
												
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

LANGS = deskbar.locale_utils.get_languages()
def get_entry_locale(config, key):
	for lang in LANGS:
		locale_key = "%s[%s]" % (key, lang)
		try:
			return config.get("Desktop Entry", locale_key, True)
		except:
			pass
	
	return config.get("Desktop Entry", key, True)
