import re,cgi, urllib, os
from gettext import gettext as _
import gnomevfs, gconf, gtk, gobject, os.path
import deskbar, deskbar.Match, deskbar.Utils

def is_preferred_browser(test):
	# We will import only if the user's preferred browser is mozilla
	http_handler = gconf.client_get_default().get_string("/desktop/gnome/url-handlers/http/command").strip().lower()
	if not gconf.client_get_default().get_bool("/desktop/gnome/url-handlers/http/enabled"):
		return False
	
	if http_handler.find(test) != -1:
		return True
	
	http_handler = http_handler.split(" ")[0]

	paths = [path for path in os.getenv("PATH").split(os.path.pathsep) if path.strip() != "" and os.path.exists(path) and os.path.isdir(path)]
	for directory in paths:
		if http_handler.startswith("/"):
			program_path = http_handler
		else:
			program_path = os.path.join(directory, http_handler)
		
		while os.path.islink(program_path):
			program_path = os.path.join(directory, os.readlink(program_path))
			directory = os.path.dirname(program_path)
		
		if program_path.find(test) != -1:
			return True
	
	return False
		
class BrowserMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, url=None, is_history=False, **args):
		deskbar.Match.Match.__init__(self, backend, name=cgi.escape(name), **args)
		self._priority = 10
		
		self.url = url
		self.is_history = is_history
		
	def action(self, text=None):
		gnomevfs.url_show(self.url)
		
	def get_verb(self):
		if self.is_history:
			return _("Open History Item %s") % "<b>%(name)s</b>"
		else:
			return _("Open Bookmark %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.url
	
	def get_category(self):
		return "web"
		
class BrowserSmartMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, url=None, prefix_to_strip=None, bookmark=None, serialized_bookmark=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=cgi.escape(name), **args)
		self._priority = 0
		
		self.url = url
		if bookmark != None:
			self._bookmark = bookmark
			self.serialized_bookmark = bookmark.serialize()
		else:
			self._bookmark = BrowserMatch(backend, **serialized_bookmark)
			self.serialized_bookmark = serialized_bookmark
		
		self.prefix_to_strip = prefix_to_strip
		if self.prefix_to_strip != None and not self.prefix_to_strip.endswith(" "):
			self.prefix_to_strip += " "
	
	def get_bookmark(self):
		return self._bookmark
		
	def get_hash(self, text=None):
		return self.url
	
	def get_category(self):
		return "websearch"
		
	def get_name(self, text=None):
		m = deskbar.Match.Match.get_name(self, text)
		if self.prefix_to_strip != None and text.startswith(self.prefix_to_strip):
			m["text"] = text[len(self.prefix_to_strip):]
		return m
		
	def action(self, text=""):
		if self.prefix_to_strip != None and text.startswith(self.prefix_to_strip):
			text = text[len(self.prefix_to_strip):]
		
		real_url = re.sub("%s", urllib.quote_plus(text), self.url)
		gnomevfs.url_show(real_url)
		
	def get_verb(self):
		#translators: First %s is the search engine name, second %s is the search term
		return _("Search <b>%(name)s</b> for <i>%(text)s</i>")
				
def get_url_host(url):
	try:
		#Remove http: needed by splithost
		clean = url[url.find(":")+1:]
		
		#Remove the www part so we have more matches
		if clean.startswith("//www."):
			clean = "//"+clean[6:]
			
		return urllib.splithost(clean)[0]
	except Exception, msg:
		print 'Error:get_url_host(%s):%s' % (url, msg)
		return url


# FIXME: Begins nastyness:
# Definitions from here down deal with shortcuts for smart bookmarks - both
# managing the UI for customizing shortcuts, and methods for activating them
# on the right triggers (e.g. Ctrl-something).

def on_entry_key_press(query, shortcut, shortcuts_to_smart_bookmarks_map):
	key = chr(shortcut)
	try:
		bookmark = shortcuts_to_smart_bookmarks_map[key]
		return bookmark
	except KeyError:
		# There was no shortcut defined for this keypress
		return None

def _sync_shortcuts_map_from_list_store(list_store, smart_bookmarks, shortcuts_to_smart_bookmarks_map):
	shortcuts_to_smart_bookmarks_map.clear()
	for row in list_store:
		shortcut, smart_bookmark = row[0], row[1]
		if shortcut != None and len(shortcut) > 0:
			shortcuts_to_smart_bookmarks_map[shortcut] = smart_bookmark

def _sync_list_store_from_shortcuts_map(list_store, smart_bookmarks, shortcuts_to_smart_bookmarks_map):
	# m is the inverse map of shortcuts_to_smart_bookmarks_map
	m = {}
	for sc in shortcuts_to_smart_bookmarks_map.keys():
		m[shortcuts_to_smart_bookmarks_map[sc]] = sc
	
	# FIXME: this is a major design flaw since not inited bookmarks will fail here
	# FIXME: Another fixme is to resolve conflicts in keybindings, and probably we
	# should provide an unified framework to bind shortcuts with register/unregiter things
	if smart_bookmarks == None:
		return
		
	for b in smart_bookmarks:
		try:
			list_store.append([m[b], b])
		except KeyError:
			# The smart bookmark b did not have a shortcut
			list_store.append([None, b])

def load_shortcuts(smart_bookmarks, shortcuts_to_smart_bookmarks_map):
	shortcuts_to_smart_bookmarks_map.clear()
	url_to_shortcuts = {}
	try:
		for line in file(os.path.join(deskbar.USER_DESKBAR_DIR, "search-bookmarks-shortcuts.txt")):
			line = line.strip()
			if len(line) > 0:
				url, shortcut = line.split()
				url_to_shortcuts[url] = shortcut
	except IOError:
		# The file probably does not exist
		pass
	for b in smart_bookmarks:
		try:
			sc = url_to_shortcuts[b.url]
			shortcuts_to_smart_bookmarks_map[sc] = b
		except KeyError:
			pass

def _save_shortcuts(shortcuts_to_smart_bookmarks_map):
	f = open(os.path.join(deskbar.USER_DESKBAR_DIR, "search-bookmarks-shortcuts.txt"), "w")
	for shortcut in shortcuts_to_smart_bookmarks_map.keys():
		bookmark = shortcuts_to_smart_bookmarks_map[shortcut]
		f.write(bookmark.url)
		f.write("\t")
		f.write(shortcut)
		f.write("\n")
	f.close()

def _on_shortcut_edited(cell, path, new_text, (list_store, smart_bookmarks, shortcuts_to_smart_bookmarks_map)):
	new_text = new_text.strip()
	if len(new_text) == 0:
		new_text = None
	list_store[path][0] = new_text
	_sync_shortcuts_map_from_list_store(list_store, smart_bookmarks, shortcuts_to_smart_bookmarks_map)
	_save_shortcuts(shortcuts_to_smart_bookmarks_map)

def on_customize_search_shortcuts(smart_bookmarks, shortcuts_to_smart_bookmarks_map):
	list_store = gtk.ListStore(str, gobject.TYPE_PYOBJECT)
	_sync_list_store_from_shortcuts_map(list_store, smart_bookmarks, shortcuts_to_smart_bookmarks_map)
	
	glade = gtk.glade.XML(os.path.join(deskbar.SHARED_DATA_DIR, "smart-bookmarks.glade"))
	
	view = glade.get_widget("bookmarks-view")
	view.set_model(list_store)
	
	crt_shortcut = gtk.CellRendererText()
	crt_shortcut.set_property("editable", True)
	crt_shortcut.connect("edited", _on_shortcut_edited, (list_store, smart_bookmarks, shortcuts_to_smart_bookmarks_map))
	tvc_shortcut = gtk.TreeViewColumn(_("Shortcut"), crt_shortcut, text=0)
	view.append_column(tvc_shortcut)
	
	def bookmark_to_bookmark_name(tree_view_column, cell_renderer, model, iter):
		bookmark = model.get_value(iter, 1)
		cell_renderer.set_property("text", bookmark.name)

	crt_name = gtk.CellRendererText()
	tvc_name = gtk.TreeViewColumn(_("Bookmark Name"), crt_name)
	tvc_name.set_cell_data_func(crt_name, bookmark_to_bookmark_name)
	view.append_column(tvc_name)
	
	dialog = glade.get_widget("smart-bookmarks")
	dialog.set_icon(deskbar.Utils.load_icon("deskbar-applet-small.png"))
	dialog.show_all()
	dialog.run()
	dialog.destroy()
