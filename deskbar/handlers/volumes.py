import os, sys, cgi
import ConfigParser
from os.path import join, exists
from gettext import gettext as _

from deskbar.defs import VERSION

import gobject

import deskbar
from deskbar.Handler import Handler
from deskbar.Match import Match

import gtk, gnome, gnomevfs

HANDLERS = {
	"VolumeHandler" : {
		"name": _("Disks and Network Places"),
		"description": _("Open disk drives, shared network places and similar resources by name"),
		"version": VERSION,
	}
}

NETWORK_URIS = ["http", "ftp", "smb", "sftp"]
AUDIO_URIS = ["cdda"]

MONITOR = gnomevfs.VolumeMonitor()

class VolumeMatch (Match):
	def __init__(self, backend, name=None, drive=None, icon=None):
		deskbar.Match.Match.__init__(self, backend, name=name, icon=icon)
		self.drive = drive
	
	def action(self, text=None):
		gobject.spawn_async(["nautilus", self.drive], flags=gobject.SPAWN_SEARCH_PATH)
	
	def is_valid(self, text=None):
		return exists(self.drive)
		
	def get_category(self):
		return "places"
	 
	def get_verb(self):
		if self.drive == None:
			uri_scheme = None
		else:
			uri_scheme = gnomevfs.get_uri_scheme(self.drive) 
			
		if uri_scheme in NETWORK_URIS:
			return _("Open network place %s") % "<b>%(name)s</b>"
		elif uri_scheme in AUDIO_URIS:
			return _("Open audio disk %s") % "<b>%(name)s</b>"
		else:
			return _("Open location %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.drive
		
class VolumeHandler (Handler):
	
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "gnome-dev-harddisk")
		self.__locations = []
		
	def query(self, query):
		result = []
		query = query.lower()
		
		# We search both mounted_volumes() and connected_drives.
		# This way an audio cd in the cd drive will show up both
		# on "au" and "cd".
		# Drives returned by mounted_volumes() and connected_drives()
		# does not have the same display_name() strings.
		for drive in MONITOR.get_mounted_volumes() + MONITOR.get_connected_drives():
			if not drive.is_user_visible() : continue
			if not drive.is_mounted () : continue
			if not drive.get_display_name().lower().startswith(query): continue
			
			result.append (VolumeMatch (self, drive.get_display_name(), drive.get_activation_uri(), drive.get_icon()))
		
		return result
