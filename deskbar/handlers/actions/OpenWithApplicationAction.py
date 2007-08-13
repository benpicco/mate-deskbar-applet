import deskbar.interfaces.Action
from gettext import gettext as _
from deskbar.core.Utils import spawn_async
from os.path import exists

class OpenWithApplicationAction(deskbar.interfaces.Action):
    
    def __init__(self, name, program, arguments):
        deskbar.interfaces.Action.__init__(self, name)
        self._program = program
        if arguments != None and len(arguments) > 0:
            self._arguments = arguments
        else:
            self._arguments = []
    
    def get_icon(self):
        return "gtk-open"
    
    def is_valid(self):
        return exists(self._program)
       
    def get_hash(self):
        return self._program+" ".join(self._arguments)
        
    def get_verb(self):
        return _("Open <b>%(name)s</b> with <b>%(program)s</b>")
    
    def get_name(self, text=None):
        return {"name": self._name, "program": self._program}
    
    def activate(self, text=None):
        spawn_async([self._program] + self._arguments)