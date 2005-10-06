import os, ConfigParser, cgi, re
import glob
from os.path import join, isfile, abspath, splitext, expanduser
from gettext import gettext as _

import gtk
import deskbar, deskbar.indexer
import deskbar.handler

EXPORTED_CLASS = "PathProgramsHandler"
NAME = _("Programs in your $PATH")

PRIORITY = 100
		
class PathProgramMatch(deskbar.handler.Match):
	def __init__(self, backend, name):
		deskbar.handler.Match.__init__(self, backend, name)
		
	def action(self, text=None):
		self._priority = self._priority+1
		if text == None:
			os.spawnlp(os.P_NOWAIT, self._name, self._name)
		else:
			args = text.split(" ")[1:]
			args.insert(0, self._name)
			os.spawnvp(os.P_NOWAIT, self._name, args)
	
	def get_verb(self):
		return _("Execute <b>%(text)s</b>")

class PathProgramsHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "generic.png")
		
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
			if path.strip() == "":
				continue
				
			try:
				for program in [f for f in os.listdir(path) if isfile(join(path, f))]:
					self._programs[program] = PathProgramMatch(self, program)
			except Exception, msg:
				print 'Error:_scan_path:', msg
		
