import os, sys, cgi
import ConfigParser
from os.path import join
from gettext import gettext as _

import deskbar
from deskbar.handler import Handler
from deskbar.handler import Match

import gtk, gnome, gnomevfs

HANDLERS = {
	"VolumeHandler" : {
		"name": _("Search for Volumes"),
		"description": _("Open drives and volumes by their name"),
	}
}

icon_theme = gtk.icon_theme_get_default()

NETWORK_URIS = ["http", "ftp", "smb", "sftp"]
AUDIO_URIS = ["cdda"]

class VolumeMatch (Match):
	def __init__(self, backend, drive, icon=None):
		deskbar.handler.Match.__init__(self, backend, drive.get_display_name(), icon)
		self.__drive = drive
	
	def action(self, text=None):
		self._priority = self._priority+1
		os.spawnlp(os.P_NOWAIT, "nautilus", "nautilus", self.__drive.get_activation_uri())
	 
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
		
	def query(self, query, max=5):
		result = []
		query = query.lower()
		
		# We search both mounted_volumes() and connected_drives.
		# This way an audio cd in the cd drive will show up both
		# on "au" and "cd".
		# Drives returned by mounted_volumes() and connected_drives()
		# does not have the same display_name() strings.
		for drive in gnomevfs.VolumeMonitor().get_mounted_volumes() + gnomevfs.VolumeMonitor().get_connected_drives():
			if not drive.is_user_visible() : continue
			if not drive.is_mounted () : continue
			if not drive.get_display_name().lower().startswith(query): continue
			
			icon = None
			try:
				icon = icon_theme.load_icon(drive.get_icon(), deskbar.ICON_SIZE, gtk.ICON_LOOKUP_USE_BUILTIN)
			except Exception, msg:
				print "Error:volumes.py:%s" % msg

			result.append (VolumeMatch (self, drive, icon))
		
		return result[:max]
