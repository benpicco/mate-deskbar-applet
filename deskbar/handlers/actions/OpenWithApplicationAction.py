import deskbar.interfaces.Action
from gettext import gettext as _
from deskbar.core.Utils import spawn_async, is_program_in_path
from os.path import exists, isabs

class OpenWithApplicationAction(deskbar.interfaces.Action):
    
    def __init__(self, name, program, arguments, display_program_name=None):
        deskbar.interfaces.Action.__init__(self, name)
        self._program = program
        if arguments != None and len(arguments) > 0:
            self._arguments = arguments
        else:
            self._arguments = []
        if display_program_name == None:
            self._display_program_name = program
        else:
            self._display_program_name = display_program_name
    
    def get_icon(self):
        return "gtk-open"
    
    def is_valid(self):
        if isabs(self._program):
            return exists(self._program)
        else:
            return is_program_in_path(self._program)
       
    def get_hash(self):
        return self._program+" ".join(self._arguments)
        
    def get_verb(self):
        return _("Open <b>%(name)s</b> with <b>%(program)s</b>")
    
    def get_name(self, text=None):
        return {"name": self._name, "program": self._display_program_name}
    
    def activate(self, text=None):
        spawn_async([self._program] + self._arguments)