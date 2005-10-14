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
	def __init__(self, backend, name, duplicate=False):
		deskbar.handler.Match.__init__(self, backend, name)
		self._duplicate = duplicate
	
	def is_duplicate(self):
		return self._duplicate
		
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
		
	def initialize(self):
		self._desktop_programs = self._scan_desktop_files()
		self._scan_path()
	
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		args = query.split(" ")
		if args[0] in self._programs:
			# Either we have a duplicate program and we don't show it, unless the args exists
			if (self._programs[args[0]].is_duplicate() and len(args) > 1) or (not self._programs[args[0]].is_duplicate()):
				return [self._programs[args[0]]]		
		
		return []
	
	def _scan_desktop_files(self):
		desktop_dir = abspath(join("/", "usr", "share", "applications"))
		
		desktop_programs = []
		for f in glob.glob(desktop_dir + '/*.desktop'):
			try:
				config = ConfigParser.SafeConfigParser()
				config.read(f)

				desktop_programs.append(config.get("Desktop Entry", "Exec", True).split(' ', 1)[0])
			except Exception, msg:
				print 'Error:_scan_desktop_files(pathprograms.py):File Error:%s:%s' % (f, msg)
				continue
		
		return desktop_programs
				
	def _scan_path(self):
		for path in os.getenv("PATH").split(os.path.pathsep):
			if path.strip() == "":
				continue
				
			try:
				for program in [f for f in os.listdir(path) if isfile(join(path, f))]:
					if program in self._desktop_programs:
						self._programs[program] = PathProgramMatch(self, program, True)
					else:
						self._programs[program] = PathProgramMatch(self, program)
			except Exception, msg:
				print 'Error:_scan_path:', msg
		
