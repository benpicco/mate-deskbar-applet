from deskbar.core.Utils import get_xdg_data_dirs, is_program_in_path, spawn_async, is_executable, PATH
from deskbar.defs import VERSION
from deskbar.handlers.actions.OpenDesktopFileAction import OpenDesktopFileAction, parse_desktop_file, parse_desktop_filename
from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from gettext import gettext as _
from os.path import join, expanduser, isdir
from os import stat
import deskbar, deskbar.core.Indexer
import deskbar.core.Utils
import gnomedesktop
import deskbar.interfaces.Action
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import glob
import glib
import gtk
import os
import re
import time

HANDLERS = [
    "ProgramsHandler",
    "GnomeDictHandler",
    "GnomeSearchHandler",
    "DevhelpHandler"]

EXACT_MATCH_PRIO = 50
EXACT_WORD_PRIO = 5
DESKTOP_FILE_PRIO = 25

class GenericAction(OpenWithApplicationAction):
    
    def __init__(self, name, program, args, verb):
        OpenWithApplicationAction.__init__(self, name, program, args)
        self._verb = verb
        
    def activate(self, text=None):
        self._arguments += [text]
        OpenWithApplicationAction.activate(self, text)
        # Restore old arguments
        del self._arguments[-1]
        
    def get_verb(self):
        return self._verb

class GenericProgramMatch(deskbar.interfaces.Match):
    def __init__(self, arguments=[], desktop=None, desktop_file=None, verb="", **args):
        deskbar.interfaces.Match.__init__(self, category="actions", **args)
        
        self.desktop_file = desktop_file
        self._args = arguments
        self.verb = verb
        
        self.set_priority(self.get_priority() + EXACT_WORD_PRIO)
        
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
        self._display_prog = exe.strip()
        
        if len(self._args) > 0:
            program = self._desktop.get_string("Exec")
            self.add_action( GenericAction(self.get_name(), program, self._args, verb) )
        else:
            self.add_action( OpenDesktopFileAction(self.get_name(), self._desktop, self.desktop_file, self._display_prog) )

    def get_hash(self):
        return "generic_"+self._display_prog
    
    def get_program(self):
        return self._display_prog
        
class GnomeDictMatch(GenericProgramMatch):
    def __init__(self, **args):
        GenericProgramMatch.__init__(self,
            arguments = ["--look-up"],
            verb=_("Lookup %s in dictionary") % "<b>%(text)s</b>",
            **args) 

class GnomeSearchMatch(GenericProgramMatch):
    def __init__(self, **args):
        GenericProgramMatch.__init__(self,
            arguments=["--start", "--path", expanduser("~"), "--named"],
            verb=_("Search for file names like %s") % "<b>%(text)s</b>",
            **args)
    
class DevhelpMatch(GenericProgramMatch):
    def __init__(self, **args):
        GenericProgramMatch.__init__(self, arguments = ["-s"],
            verb=_("Search in Devhelp for %s") % "<b>%(text)s</b>",                
            **args) 

class SpecialProgramHandler(deskbar.interfaces.Module):
    
    def __init__(self, desktop_file):
        deskbar.interfaces.Module.__init__(self)
        self._desktop_file = desktop_file
        self._match = None
        
    def initialize(self):
        result = parse_desktop_filename(self._desktop_file, False)
        if result != None:
            self._match = self.create_match(result, self._desktop_file)
    
    def create_match(self, desktop, f):
        raise NotImplementedError
        
    def query(self, qstring):
        if self._match != None:
            self._match.set_priority( self.get_priority() + get_priority_for_name(qstring, self._match._desktop.get_string("Exec")) )
            self._emit_query_ready(qstring, [self._match] )
            
    @staticmethod
    def desktop_file_exists(desktop):
        for dir in get_xdg_data_dirs():
            f = os.path.join(dir, "applications", desktop)
            if os.path.exists(f):
                return True
        return False
        
class GnomeDictHandler(SpecialProgramHandler):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon('accessories-dictionary'),
             'name': _("Dictionary"),
             'description': _("Look up word definitions in the dictionary"),
             'version': VERSION}
    
    def __init__(self):
        SpecialProgramHandler.__init__(self, "gnome-dictionary.desktop")
    
    def create_match(self, desktop, f):
        return GnomeDictMatch(
                    name=desktop.get_localestring(gnomedesktop.KEY_NAME),
                    icon=desktop.get_string(gnomedesktop.KEY_ICON),
                    desktop=desktop,
                    desktop_file=f)
        
    @staticmethod
    def has_requirements():
        if not SpecialProgramHandler.desktop_file_exists("gnome-dictionary.desktop"):
            DevhelpHandler.INSTRUCTIONS = _("GNOME dictionary is not installed")
            return False
        return True
        
class GnomeSearchHandler(SpecialProgramHandler):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon('system-search'),
             'name': _("Files and Folders Search"),
             "description": _("Find files and folders by searching for a name pattern"),
             'version': VERSION}
    
    def __init__(self):
        SpecialProgramHandler.__init__(self, "gnome-search-tool.desktop")
    
    def create_match(self, desktop, f):
        return GnomeSearchMatch(
                    name=desktop.get_localestring(gnomedesktop.KEY_NAME),
                    icon=desktop.get_string(gnomedesktop.KEY_ICON),
                    desktop=desktop,
                    desktop_file=f)
        
    @staticmethod
    def has_requirements():
        if not SpecialProgramHandler.desktop_file_exists("gnome-search-tool.desktop"):
            DevhelpHandler.INSTRUCTIONS = _("GNOME search tool is not installed")
            return False
        return True
        
class DevhelpHandler(SpecialProgramHandler):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon('devhelp'),
             "name": _("Developer Documentation"),
             "description": _("Search Devhelp for a function name"),
             'version': VERSION}
    
    def __init__(self):
        if SpecialProgramHandler.desktop_file_exists("devhelp.desktop"):
        	SpecialProgramHandler.__init__(self, "devhelp.desktop")
        else:
      		SpecialProgramHandler.__init__(self, "gnome-devhelp.desktop")
    
    def create_match(self, desktop, f):
        return DevhelpMatch(
                    name=desktop.get_localestring(gnomedesktop.KEY_NAME),
                    icon=desktop.get_string(gnomedesktop.KEY_ICON),
                    desktop=desktop,
                    desktop_file=f)
        
    @staticmethod
    def has_requirements():
        if not (SpecialProgramHandler.desktop_file_exists("devhelp.desktop") or SpecialProgramHandler.desktop_file_exists("gnome-devhelp.desktop")):
            DevhelpHandler.INSTRUCTIONS = _("Devhelp is not installed")
            return False
        return True

class OpenPathProgramAction(deskbar.interfaces.Action):
    
    def __init__(self, name, use_terminal):
        deskbar.interfaces.Action.__init__(self, name)
        self.use_terminal = use_terminal
        
    def get_icon(self):
        return "gtk-execute"
        
    def activate(self, text=None):
        if self.use_terminal:
            try:
                import subprocess

                prog = subprocess.Popen(
                    self._name.split(" "),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                
                zenity = subprocess.Popen(
                    ["zenity", "--title="+self._name,
                        "--window-icon="+join(deskbar.ART_DATA_DIR, "generic.png"),
                        "--width=700",
                        "--height=500",
                        "--text-info"],
                    stdin=prog.stdout)
    
                # Reap the processes when they have done
                glib.child_watch_add(zenity.pid, lambda pid, code: None)
                glib.child_watch_add(prog.pid, lambda pid, code: None)
                return
            except:
                #No zenity, get out of the if, and launch without GUI
                pass
        
        spawn_async(self._name.split(" "))
        
    def get_hash(self):
        if self.use_terminal:
            return self._name + "_terminal"
        else:
            return self._name

    def get_verb(self):
        if self.use_terminal:
            return _("Execute %s in terminal") % "<b>%(name)s</b>"
        else:
            return _("Execute %s") % "<b>%(name)s</b>"

class PathProgramMatch(deskbar.interfaces.Match):
    
    def __init__(self, name, command, priority=0, **args):
        deskbar.interfaces.Match.__init__(self, name=name, icon="gtk-execute", category="actions", **args)
        self.set_priority(self.get_priority() + EXACT_MATCH_PRIO)
        self.add_action( OpenPathProgramAction(command, False), True )
        self.add_action( OpenPathProgramAction(command, True) )
        
    def get_hash(self):
        return self._name
   
class StartsWithPathProgramMatch(deskbar.interfaces.Match):
    
    def __init__(self, command, priority=0, **args):
        deskbar.interfaces.Match.__init__(self, name=command, icon="gtk-execute", category="actions", **args)
        self._command = command
        self.add_action( OpenPathProgramAction(command, False), True )
        self.add_action( OpenPathProgramAction(command, True) )
        
    def get_hash(self):
        return self._command
        
class ProgramsHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon(gtk.STOCK_EXECUTE),
             "name": _("Programs"),
             "description": _("Launch a program by its name and/or description"),
             'version': VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self._indexer = deskbar.core.Indexer.Indexer()
        self._path_indexers = {}
        
    def initialize(self):
        self._scan_desktop_files()
        self._scan_path_directories()

    def query(self, query):
        result = self.query_desktop_programs(query)
        
        desktop_progs = set()
        for match in result:
            desktop_progs.add( match.get_program () )
            match.set_priority (self.get_priority() + DESKTOP_FILE_PRIO + match.get_priority())
        
        path_result = self.query_path_programs(query, desktop_progs)
        result += path_result
        
        self._emit_query_ready(query, result )
        
    def query_path_programs(self, query, desktop_progs):
        """
        @param query: Query string
        @param desktop_progs: Names of binaries from .desktop files
        """
        args = query.split(" ")     
        program = args[0]
        priority = self.get_priority()

        if len(args) == 1:
            results = []
            for pathdir in PATH:
                try:
                    pathstat = stat(pathdir)
                    pathmtime = pathstat.st_mtime
                except OSError:
                    continue

                indexpair = self._path_indexers.get(pathdir, None)
                if indexpair is not None:
                    indexer, updatetime = indexpair
                else:
                    indexer, updatetime = deskbar.core.Indexer.Indexer(), -1
                if pathmtime > updatetime:
                    self._scan_path(pathdir, indexer)
                    self._path_indexers[pathdir] = (indexer, time.time())
                for match in indexer.look_up(program):
                    if match.get_hash() in desktop_progs:
                        continue
                    match.set_priority(priority + get_priority_for_name(query, program))
                    results.append(match)

            return results
        else:
            # We have arguments, execute the command as typed in by the user
            if not (program in desktop_progs) and is_program_in_path(program):
                match = PathProgramMatch(program, query)
                match.set_priority (self.get_priority() + EXACT_MATCH_PRIO)
                return [match]
            else:
                return []
    
    def query_desktop_programs(self, query):
        result = []
        for match in self._indexer.look_up(query):
            match.set_priority (get_priority_for_name(query, match._desktop.get_string("Exec")))
            result.append(match)
        return result

    def _scan_path_directories(self):
        for pathdir in PATH:
            if isdir(pathdir) and is_executable(pathdir):
                indexer = deskbar.core.Indexer.Indexer()
                self._scan_path(pathdir, indexer)
                self._path_indexers[pathdir] = (indexer, time.time())

    def _scan_path(self, path, indexer):
        if isdir(path) and is_executable(path):
            for f in os.listdir(path):
                pathprog = join(path, f)
                if not isdir(pathprog) and is_executable(pathprog):
                    match = StartsWithPathProgramMatch(f)
                    indexer.add(f, match)

    def _scan_desktop_files(self):
        for dir in get_xdg_data_dirs():
            for root, dirs, files in os.walk( join(dir, "applications") ):
                for f in glob.glob( join(root, "*.desktop") ):
                    result = parse_desktop_file(f)
                    if result != None:
                        match = GenericProgramMatch(
                                    name=result.get_localestring(gnomedesktop.KEY_NAME),
                                    icon=result.get_string(gnomedesktop.KEY_ICON),
                                    desktop=result,
                                    desktop_file=f)
                        self._indexer.add("%s %s %s %s %s" % (
                                    result.get_string("Exec"),
                                    result.get_localestring(gnomedesktop.KEY_NAME),
                                    result.get_localestring(gnomedesktop.KEY_COMMENT),
                                    result.get_string(gnomedesktop.KEY_NAME),
                                    result.get_string(gnomedesktop.KEY_COMMENT),
                                ), match)

def get_priority_for_name(query, name):
    bin = name.split(" ")[0]
    if bin == query:
        return EXACT_MATCH_PRIO
    else:
        return EXACT_WORD_PRIO
