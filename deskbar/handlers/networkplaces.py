from gettext import gettext as _
import os
import gconf, gtk
import deskbar.handler, deskbar.indexer

EXPORTED_CLASS = "NetworkPlacesHandler"
NAME = (_("Network Places"), "Network Places")

PRIORITY = 150

NETWORK_PLACES_GCONF = '/desktop/gnome/connected_servers'

icon_theme = gtk.icon_theme_get_default()

class NetworkPlacesMatch(deskbar.handler.Match):
	def __init__(self, backend, name, uri, icon):
		deskbar.handler.Match.__init__(self, backend, name, icon)
		self._uri = uri
		
	def action(self, text=None):
		self._priority = self._priority+1
		os.spawnlp(os.P_NOWAIT, "nautilus", "nautilus", self._uri)
	
	def get_verb(self):
		return _("Open network place <b>%(name)s</b>")
		
	
class NetworkPlacesHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "folder-bookmark.png")
		
		self._indexer = deskbar.indexer.Index()
		
	def initialize_safe(self):
		self._scan_network_places()
		
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		return self._indexer.look_up(query)[:max]
		
	def _scan_network_places(self):
		client = gconf.client_get_default()
		if not client.dir_exists(NETWORK_PLACES_GCONF):
			return
		
		dirs = client.all_dirs(NETWORK_PLACES_GCONF)
		for place in dirs:
			try:
				name = client.get_string(place+"/display_name")
				uri = client.get_string(place+"/uri")
				
				pixbuf = None
				try:
					icon = client.get_string(place+"/icon")
					pixbuf = icon_theme.load_icon(icon, deskbar.ICON_SIZE, gtk.ICON_LOOKUP_USE_BUILTIN)
				except Exception, msg:
					print 'Error:_scan_network_places:Cannot retreive icon:', msg
				
				self._indexer.add(name, NetworkPlacesMatch(self, name, uri, pixbuf))
			except Exception, msg:
				print 'Error:_scan_network_places:', msg
