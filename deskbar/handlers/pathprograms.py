import os, ConfigParser, cgi, re
import glob
from os.path import join, isfile, abspath, splitext, expanduser, exists, isdir
from gettext import gettext as _

import gobject
import gtk
import deskbar, deskbar.indexer
import deskbar.handler

HANDLERS = {
	"PathProgramsHandler" : {
		"name": _("Programs (Advanced)"),
		"description": _("Launch any program present in your $PATH"),
	}
}

class PathProgramMatch(deskbar.handler.Match):
	def __init__(self, backend, name):
		deskbar.handler.Match.__init__(self, backend, name)
	
	def get_hash(self, text=None):
		return text
		
	def action(self, text=None):
		gobject.spawn_async(text.split(" "), flags=gobject.SPAWN_SEARCH_PATH)
	
	def get_verb(self):
		return _("Execute %s") % "<b>%(text)s</b>"

class PathProgramsHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "generic.png")
		
	def initialize(self):
		self._path = [path for path in os.getenv("PATH").split(os.path.pathsep) if path.strip() != "" and exists(path) and isdir(path)]
		
	def query(self, query, max=5):
		args = query.split(" ")
		match = self._check_program(args[0])

		if match != None:
			return [match]
		else:
			return []
			
	def _check_program(self, program):
		for path in self._path:
			prog_path = join(path, program)
			if exists(prog_path) and isfile(prog_path):
				return PathProgramMatch(self, program)	
								
