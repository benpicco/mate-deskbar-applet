import os, ConfigParser, cgi, re
import glob
from os.path import join, isfile, abspath, splitext, expanduser, exists, isdir
from gettext import gettext as _

import gtk
import deskbar, deskbar.indexer
import deskbar.handler

HANDLERS = {
	"PathProgramsHandler" : {
		"name": _("Command line programs"),
		"description": _("Allow to launch any program present in your $PATH"),
	}
}

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
		
	def initialize(self):
		self._path = [path for path in os.getenv("PATH").split(os.path.pathsep) if path.strip() != "" and exists(path) and isdir(path)]
		self._desktop_programs = self._scan_desktop_files()
		
	def query(self, query, max=5):
		args = query.split(" ")
		match = self._check_program(args[0])
		if match != None and ( (match.is_duplicate() and len(args) > 1) or (not match.is_duplicate()) ):
			# Either we have a duplicate program and we don't show it, unless the args exists
			return [match]
		else:
			return []
	
	def _scan_desktop_files(self):
		desktop_programs = []
		for f in glob.glob('/usr/share/applications/*.desktop'):
			try:
				config = ConfigParser.SafeConfigParser()
				config.read(f)
				desktop_programs.append(config.get("Desktop Entry", "Exec", True).split(' ', 1)[0])
			except:
				continue
		
		return desktop_programs
	
	def _check_program(self, program):
		for path in self._path:
			prog_path = join(path, program)
			if exists(prog_path) and isfile(prog_path):
				return PathProgramMatch(self, program, (program in self._desktop_programs))	
								
