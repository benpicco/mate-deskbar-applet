import os, sys
import ConfigParser
import gnomevfs
import deskbar
from deskbar.handler import Handler
from deskbar.handler import Match
from gettext import gettext as _
import cgi
import gtk
from os.path import join

EXPORTED_CLASS = "VolumeHandler"
NAME = (_("Search for Volumes"), _("Open drives and volumes by their name"))

PRIORITY = 150
icon_theme = gtk.icon_theme_get_default()

NETWORK_URIS = ["http", "ftp", "smb", "sftp"]
AUDIO_URIS = ["cdda"]

class VolumeMatch (Match):
	def __init__(self, backend, drive, icon=None):
		deskbar.handler.Match.__init__(self, backend, drive.get_display_name(), icon)
		self.__drive = drive
	
	def action(self, text=None):
		os.spawnlp(os.P_NOWAIT, "gnome-open", "gnome-open", self.__drive.get_activation_uri())
	 
	def get_verb(self):
		uri_scheme = gnomevfs.get_uri_scheme(self.__drive.get_activation_uri()) 
		if uri_scheme in NETWORK_URIS:
			return _("Open network place <b>%(name)s</b>")
		elif uri_scheme in AUDIO_URIS:
			return _("Open audio disk <b>%(name)s</b>")
		else:
			return _("Open location <b>%(name)s</b>")

class VolumeHandler (Handler):
	
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "gnome-dev-harddisk.png")
		self.__locations = []
		
	def initialize(self):
		pass
		
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		result = []
		query = query.lower()
				
		for drive in gnomevfs.VolumeMonitor().get_mounted_volumes() + gnomevfs.VolumeMonitor().get_connected_drives():
			if not drive.is_user_visible() : continue
			if not drive.is_mounted () : continue
			if not drive.get_display_name().lower().startswith(query): continue
			
			#iconfile = join(deskbar.ART_DATA_DIR, drive.get_icon()) + ".png"
			icon = None
			try:
				icon = icon_theme.load_icon(drive.get_icon(), deskbar.ICON_SIZE, gtk.ICON_LOOKUP_USE_BUILTIN)
			except Exception, msg:
				print "Error:volumes.py:%s" % msg

			result.append (VolumeMatch (self, drive, icon))
		
		return result[:max]
