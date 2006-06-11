from gettext import gettext as _
from gettext import ngettext
from deskbar.defs import VERSION
import wnck, gtk
import deskbar.Handler, deskbar
import re
import cgi

HANDLERS = {
	"ISwitchWindowHandler" : {
		"name": _("Window Switcher"),
		"description": _("Switch to an existing window by name."),

		"categories" : {
			"windows"	: {
				"name": _("Windows"),
				"nest": lambda n: ngettext("%s more window", "%s more windows", n),
				"threshold": 10
				}
			},
		"version": VERSION,
			
		}
	}

class ISwitchWindowMatch(deskbar.Match.Match):
	def __init__(self, handler, window=None, pixbuf=None, **args):
		deskbar.Match.Match.__init__ (self, handler, **args)
		self.name = cgi.escape(self.name)
		self._icon = pixbuf
		self._window = window

	def get_verb(self):
		return _("Switch to <b>%(name)s</b>")

	def action(self, text=None):
		if self._window.is_active():
			return
		
		if self._window.get_workspace() != self._window.get_screen().get_active_workspace():
			self._window.get_workspace().activate(gtk.get_current_event_time())

		self._window.activate(gtk.get_current_event_time())

	def get_category(self):
		return "windows"

	def get_hash(self, text=None):
		return self.name

	def serialize(self):
		return None
	
	def skip_history(self):
		return True

class ISwitchWindowHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "panel-window-menu.png")

	def query(self, query):
		results = []
		query = query.lower()
		for w in wnck.screen_get_default().get_windows_stacked():
				if w.is_skip_tasklist():
						continue
				
				for name in (w.get_name().lower(), w.get_application().get_name().lower()):
						if name.find(query) != -1:
								results.append(ISwitchWindowMatch(self, name=name, window=w, pixbuf=w.get_mini_icon()))
								break

		return results
