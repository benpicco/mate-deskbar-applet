"""
Stores the Preferences per-applet or shared across applets
"""
import gconf
import deskbar

class DeskbarAppletPreferences:
	def __init__(self, applet):
		# Default values
		self.GCONF_APPLET_DIR = deskbar.GCONF_DIR
		self.GCONF_WIDTH = deskbar.GCONF_WIDTH
		self.GCONF_EXPAND = deskbar.GCONF_EXPAND
		self.GCONF_UI_NAME = deskbar.GCONF_UI_NAME
		
		# This preference is shared across all applet instances, unlike
		# width, which is per-instance.
		self.GCONF_KEYBINDING = deskbar.GCONF_KEYBINDING
		
		# Retreive this applet's pref folder
		path = applet.get_preferences_key()
		if path != None:
			self.GCONF_APPLET_DIR = path
			self.GCONF_WIDTH =  self.GCONF_APPLET_DIR + "/width"
			self.GCONF_EXPAND = self.GCONF_APPLET_DIR + "/expand"
			self.GCONF_UI_NAME = self.GCONF_APPLET_DIR + "/ui_name"
			
			applet.add_preferences("/schemas" + deskbar.GCONF_DIR)
			deskbar.GCONF_CLIENT.add_dir(self.GCONF_APPLET_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)
			
			print 'Using per-applet gconf key:', self.GCONF_APPLET_DIR
		
