from gettext import gettext as _
import os
import gconf, gtk
import deskbar.handler, deskbar.indexer

EXPORTED_CLASS = "NetworkPlacesHandler"
NAME = _("Network Places")

PRIORITY = 150

GCONF_CLIENT = gconf.client_get_default()
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
		
		print 'Starting Network places file indexation'
		self._indexer = deskbar.indexer.Index()
		self._scan_network_places()
		print '\tDone !'
		
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		return self._indexer.look_up(query)[:max]
		
	def _scan_network_places(self):
		if not GCONF_CLIENT.dir_exists(NETWORK_PLACES_GCONF):
			return
			
		dirs = GCONF_CLIENT.all_dirs(NETWORK_PLACES_GCONF)
		for place in dirs:
			try:
				name = GCONF_CLIENT.get_string(place+"/display_name")
				uri = GCONF_CLIENT.get_string(place+"/uri")
				
				pixbuf = None
				try:
					icon = GCONF_CLIENT.get_string(place+"/icon")
					pixbuf = icon_theme.load_icon(icon, deskbar.ICON_SIZE, gtk.ICON_LOOKUP_USE_BUILTIN)
				except Exception, msg:
					print 'Error:_scan_network_places:Cannot retreive icon:', msg
				
				self._indexer.add(name, NetworkPlacesMatch(self, name, uri, pixbuf))
			except Exception, msg:
				print 'Error:_scan_network_places:', msg
