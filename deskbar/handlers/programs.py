import re
import glob
import os
from os.path import join, expanduser
from gettext import gettext as _
from deskbar.defs import VERSION
import gobject
import gtk
import deskbar, deskbar.core.Indexer, deskbar.core.Utils
import deskbar.interfaces.Module, deskbar.interfaces.Match, deskbar.core.gnomedesktop
from deskbar.core.Utils import get_xdg_data_dirs, is_program_in_path, spawn_async
from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from deskbar.handlers.actions.OpenDesktopFileAction import OpenDesktopFileAction, parse_desktop_file, parse_desktop_filename
import deskbar.interfaces.Action

HANDLERS = [
    "ProgramsHandler",
    "GnomeDictHandler",
    "GnomeSearchHandler",
    "DevhelpHandler"]

EXACT_MATCH_PRIO = 50
EXACT_WORD_PRIO = 5

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
                    name=desktop.get_localestring(deskbar.core.gnomedesktop.KEY_NAME),
                    icon=desktop.get_string(deskbar.core.gnomedesktop.KEY_ICON),
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
                    name=desktop.get_localestring(deskbar.core.gnomedesktop.KEY_NAME),
                    icon=desktop.get_string(deskbar.core.gnomedesktop.KEY_ICON),
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
        SpecialProgramHandler.__init__(self, "devhelp.desktop")
    
    def create_match(self, desktop, f):
        return DevhelpMatch(
                    name=desktop.get_localestring(deskbar.core.gnomedesktop.KEY_NAME),
                    icon=desktop.get_string(deskbar.core.gnomedesktop.KEY_ICON),
                    desktop=desktop,
                    desktop_file=f)
        
    @staticmethod
    def has_requirements():
        if not SpecialProgramHandler.desktop_file_exists("devhelp.desktop"):
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
        
        spawn_async(text.split(" "))
        
    def get_hash(self):
        if self.use_terminal:
            return self._name + "_terminal"
        else:
            return self._name

    def get_verb(self):
        if self.use_terminal:
            return _("Execute %s in terminal") % "<b>%(text)s</b>"
        else:
            return _("Execute %s") % "<b>%(text)s</b>"

class PathProgramMatch(deskbar.interfaces.Match):
    
    def __init__(self, name, command, priority=0, **args):
        deskbar.interfaces.Match.__init__(self, name=name, icon="gtk-execute", category="actions", **args)
        self.set_priority(self.get_priority() + EXACT_MATCH_PRIO)
        self.add_action( OpenPathProgramAction(command, False), True )
        self.add_action( OpenPathProgramAction(command, True) )
        
    def get_hash(self, text=None):
        return text
        
class ProgramsHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon(gtk.STOCK_EXECUTE),
             "name": _("Programs"),
             "description": _("Launch a program by its name and/or description"),
             'version': VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self._indexer = deskbar.core.Indexer.Indexer()
        
    def initialize(self):
        self._scan_desktop_files()
        
    def query(self, query):
        result = self.query_path_programs(query)
        result += self.query_desktop_programs(query)
        self.set_priority_for_matches(result)
        self._emit_query_ready(query, result )
        
    def query_path_programs(self, query):
        program = query.split(" ")[0]
        if is_program_in_path(program):
            return [PathProgramMatch(program, query)]
        else:
            return []
    
    def query_desktop_programs(self, query):
        result = []
        for match in self._indexer.look_up(query):
            match._priority = get_priority_for_name(query, match._desktop.get_string("Exec"))
            result.append(match)
        return result
                
    def _scan_desktop_files(self):
        for dir in get_xdg_data_dirs():
            for root, dirs, files in os.walk( join(dir, "applications") ):
                for f in glob.glob( join(root, "*.desktop") ):
                    result = parse_desktop_file(f)
                    if result != None:
                        match = GenericProgramMatch(
                                    name=result.get_localestring(deskbar.core.gnomedesktop.KEY_NAME),
                                    icon=result.get_string(deskbar.core.gnomedesktop.KEY_ICON),
                                    desktop=result,
                                    desktop_file=f)
                        self._indexer.add("%s %s %s %s %s" % (
                                    result.get_string("Exec"),
                                    result.get_localestring(deskbar.core.gnomedesktop.KEY_NAME),
                                    result.get_localestring(deskbar.core.gnomedesktop.KEY_COMMENT),
                                    result.get_string(deskbar.core.gnomedesktop.KEY_NAME),
                                    result.get_string(deskbar.core.gnomedesktop.KEY_COMMENT),
                                ), match)

def get_priority_for_name(query, name):
    if name.split(" ")[0].endswith(query):
        return EXACT_MATCH_PRIO
    else:
        return EXACT_WORD_PRIO
