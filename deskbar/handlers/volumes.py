import os, sys, cgi
import ConfigParser
from os.path import join
from gettext import gettext as _

import gobject

import deskbar
from deskbar.handler import Handler
from deskbar.handler import Match

import gtk, gnome, gnomevfs

HANDLERS = {
	"VolumeHandler" : {
		"name": _("Disks and Network Places"),
		"description": _("Open disk drives, shared network places and similar resources by name"),
	}
}

NETWORK_URIS = ["http", "ftp", "smb", "sftp"]
AUDIO_URIS = ["cdda"]

class VolumeMatch (Match):
	def __init__(self, backend, drive, icon=None):
		deskbar.handler.Match.__init__(self, backend, drive.get_display_name(), icon)
		self.__drive = drive
	
	def action(self, text=None):
		gobject.spawn_async(["nautilus", self.__drive.get_activation_uri()], flags=gobject.SPAWN_SEARCH_PATH)
	 
	def get_verb(self):
		activation = self.__drive.get_activation_uri()
		if activation == None:
			uri_scheme = None
		else:
			uri_scheme = gnomevfs.get_uri_scheme(activation) 
			
		if uri_scheme in NETWORK_URIS:
			return _("Open network place %s") % "<b>%(name)s</b>"
		elif uri_scheme in AUDIO_URIS:
			return _("Open audio disk %s") % "<b>%(name)s</b>"
		else:
			return _("Open location %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.__drive.get_activation_uri()
		
class VolumeHandler (Handler):
	
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "gnome-dev-harddisk")
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
			
			icon = deskbar.handler_utils.load_icon(drive.get_icon())
			result.append (VolumeMatch (self, drive, icon))
		
		return result[:max]
