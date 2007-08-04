import deskbar.interfaces.Action
import deskbar.core.gnomedesktop
from gettext import gettext as _

class OpenDesktopFileAction(deskbar.interfaces.Action):
    
    def __init__(self, name, desktop):
		deskbar.interfaces.Action.__init__(self, name)
		self._desktop = desktop
    
    def get_icon(self):
        return "gtk-open"
    
    def get_verb(self):
		#translators: First %s is the programs full name, second is the executable name
		#translators: For example: Launch Text Editor (gedit)
		return _("Launch <b>%(name)s</b>")
    
    def activate(self, text=None):
		try:
			self._desktop.launch([])
		except Exception, e:
			#FIXME: Proper dialog here. Also see end of Utils.py
			print 'Warning:Could not launch .desktop file:', e