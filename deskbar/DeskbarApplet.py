import os, time
from os.path import *
import gnomeapplet, gtk, gtk.gdk, gconf, gobject
from gettext import gettext as _

import deskbar, deskbar.ui
from deskbar.DeskbarHistory import get_deskbar_history
from deskbar.ModuleList import ModuleList
from deskbar.ModuleLoader import ModuleLoader
from deskbar.ui.About import show_about
from deskbar.ui.DeskbarPreferencesUI import show_preferences
from deskbar.DeskbarAppletPreferences import DeskbarAppletPreferences
from deskbar.Keybinder import get_deskbar_keybinder
from deskbar.ui.cuemiac.CuemiacButtonUI import CuemiacButtonUI
from deskbar.ui.entriac.CuemiacEntryUI import CuemiacEntryUI
from deskbar.ui.window.CuemiacWindowUI import CuemiacWindowUI


class DeskbarApplet:
	def __init__(self, applet):
		self.applet = applet
		
		self.start_query_id = 0
			
		self.prefs = DeskbarAppletPreferences(applet)
		
		self._inited_modules = 0
		self._loaded_modules = 0
		
		self._match_hashes = {}
		
		self.loader = ModuleLoader (deskbar.MODULES_DIRS)
		self.loader.connect ("modules-loaded", self.on_modules_loaded)
				
		self.module_list = ModuleList ()
		self.loader.connect ("module-loaded", self.module_list.update_row_cb)
		self.loader.connect ("module-initialized", self.module_list.module_toggled_cb)
		self.loader.connect ("module-initialized", self.on_module_initialized)
		self.loader.connect ("module-not-initialized", self.on_module_initialized)
		self.loader.connect ("module-stopped", self.module_list.module_toggled_cb)
		self.loader.connect ("module-initialized", self._connect_if_async)

		gtk.window_set_default_icon_name("deskbar-applet")

		self.minchars = deskbar.GCONF_CLIENT.get_int(self.prefs.GCONF_MINCHARS)
		if self.minchars == None:
			self.minchars = 1
		deskbar.GCONF_CLIENT.notify_add(self.prefs.GCONF_MINCHARS, lambda x, y, z, a: self.on_minchars_changed (z.value))

		self.typingdelay = deskbar.GCONF_CLIENT.get_int(self.prefs.GCONF_TYPINGDELAY)
		if self.typingdelay == None:
			self.typingdelay = 250
		deskbar.GCONF_CLIENT.notify_add(self.prefs.GCONF_TYPINGDELAY, lambda x, y, z, a: self.on_typingdelay_changed (z.value))

		# Watch out for UI override from command line
		if deskbar.UI_OVERRIDE:
			ui_name = deskbar.UI_OVERRIDE
			deskbar.GCONF_CLIENT.set_string(self.prefs.GCONF_UI_NAME, ui_name)
		else:
			# Set and retrieve the UI to be used
			ui_name = deskbar.GCONF_CLIENT.get_string(self.prefs.GCONF_UI_NAME)
			if ui_name == None:
				ui_name = deskbar.ENTRIAC_UI_NAME
		
		if ui_name == deskbar.CUEMIAC_UI_NAME:
			self.ui = CuemiacButtonUI (applet, self.prefs)
		elif ui_name == deskbar.ENTRIAC_UI_NAME:
			self.ui = CuemiacEntryUI(applet, self.prefs)
		elif ui_name == deskbar.WINDOW_UI_NAME:
			self.ui = CuemiacWindowUI(applet, self.prefs)
			self.ui.connect('show-preferences', self.on_preferences, None)
			self.ui.connect('show-about', self.on_about, None)
			self.ui.connect('clear-history', self.on_clear_history, None)
		
		# Set up the chosen UI
		self.set_up_ui_signals ()
		self.ui.set_sensitive (False)
		self.applet.add(self.ui.get_view ())
				
		deskbar.GCONF_CLIENT.notify_add (self.prefs.GCONF_UI_NAME, lambda x, y, z, a: self.on_ui_changed (z.value))
		
		# Set and retreive enabled handler list from gconf
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_ENABLED_HANDLERS, lambda x, y, z, a: self.on_config_handlers(z.value))
		
		# Monitor global shortcut binding
		get_deskbar_keybinder().connect('activated', self.on_keybinding_button_press)
		
		self.applet.connect("button-press-event", self.on_applet_button_press)
		self.applet.connect("button-release-event", self.on_applet_button_release)
		self.applet.connect('destroy', lambda x: get_deskbar_history().save())
		self.applet.setup_menu_from_file (
			deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml",
			None, [
			("About", self.on_about),
			("Prefs", self.on_preferences),
			("Clear", self.on_clear_history),
			])
		self.applet.show_all()
		
		self.loader.load_all_async()
		
	def _connect_if_async (self, sender, context):
		if context.module.is_async():
			context.module.connect ('query-ready', lambda sender, qstring, matches: self.dispatch_matches([(qstring, match) for match in matches]))	
	
	def on_match_selected (self, sender, text, match):
		print "Match selected: ",match
		self.on_stop_query()
		match.action(text)
		get_deskbar_history().add(text, match)
		
	def on_start_query (self, sender, qstring):
		if len(qstring) < self.minchars:
			return
		if self.start_query_id != 0:
			gobject.source_remove(self.start_query_id)
			
		self.start_query_id = gobject.timeout_add(self.typingdelay, self.on_start_query_real, sender, qstring)
		
	def on_start_query_real (self, sender, qstring):
		self._match_hashes = {}
		results = []
		for modctx in self.module_list:
			if not modctx.enabled:
				continue
			if modctx.module.is_async():
				modctx.module.query_async(qstring)
			else:
			
				try:
					matches = modctx.module.query(qstring)
				except TypeError:
					matches = modctx.module.query(qstring, deskbar.DEFAULT_RESULTS_PER_HANDLER)
					
				for match in matches:
					text, match = qstring, match
					if type(match) is tuple:
						text, match = match

					hsh = match.get_hash(text)
					if hsh != None:
						if hsh in self._match_hashes:
							continue
							
						self._match_hashes[hsh] = True
						results.append((text,match))
					else:
						results.append((text,match))

		if len(results) != 0:
			self.ui.append_matches (results)
	
	def dispatch_matches (self, matches):
		results = []
		for text, match in matches:
			hsh = match.get_hash(text)
			if hsh != None:
				if hsh in self._match_hashes:
					continue
					
				self._match_hashes[hsh] = True
				results.append((text,match))
			else:
				results.append((text,match))
						
		self.ui.append_matches (results)
		
	def on_stop_query (self, sender=None):
		get_deskbar_history().reset()
		if self.start_query_id != 0:
			gobject.source_remove(self.start_query_id)
				
		for modctx in self.module_list:
			if modctx.module.is_async() and modctx.enabled:
				#print "DeskbarApplet: Stopping", modctx.module,"by", sender # DEBUG
				modctx.module.stop_query()
				
	def on_request_keybinding (self, sender, match, keybinding):
		print "keybind request:", match, keybinding
		
	def on_keyboard_shortcut (self, sender, qstring, shortcut):
		for modctx in self.module_list:
			if not modctx.enabled:
				continue
				
			match = modctx.module.on_key_press(qstring, shortcut)
			if match != None:
				self.on_match_selected(sender, qstring, match)
				break
					
	def on_about (self, component, verb):
		show_about()
	
	def on_preferences (self, component, verb):
		show_preferences(self, self.loader, self.module_list)
	
	def on_clear_history (self, component, verb):
		get_deskbar_history().clear()
	
	def on_config_handlers (self, value):
		if value != None and value.type == gconf.VALUE_LIST:
			enabled_modules = [h.get_string() for h in value.get_list()]
			
			# Stop all unneeded modules
			for modctx in self.module_list:
				if modctx.enabled and not modctx.handler in enabled_modules:
					self.loader.stop_module (modctx)
			
			# Load all new modules			
			self.update_modules_priority(enabled_modules, lambda modctx: self.loader.initialize_module_async(modctx))
	
	def update_modules_priority(self, enabled_modules, callback=None):
		"""
		module_list is a module_loader.ModuleList() with loaded modules
		enabled_modules is a list of exported classnames.
		
		Update the module priority present in both module_list and enabled_modules according
		to the ordering of enabled_modules. Optionally calls callback when != None on each
		module context, in the correct order (from important to less important)
		"""
		# Compute the highest priority
		high_prio = (len(enabled_modules)-1)*100
		
		# Now we enable each gconf-enabled handler, and set it's priority according to gconf ordering
		for i, mod in enumerate(enabled_modules):
			modctx = [modctx for modctx in self.module_list if modctx.handler == mod]
			if len(modctx) != 1:
				# We have a gconf handler not on disk anymore..
				continue
				
			modctx = modctx[0]
			modctx.module.set_priority(high_prio-i*100)
			
			# Call the optional callback
			if callback != None:
				callback(modctx)
		
		self.module_list.reorder_with_priority(enabled_modules)
		
	def on_modules_loaded(self, loader):
		# Fetch the sorted handlers list from gconf
		enabled_list = deskbar.GCONF_CLIENT.get_list(deskbar.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING)
		
		def foreach_enabled(modctx):
			self.loader.initialize_module_async(modctx)
			self._loaded_modules = self._loaded_modules + 1
		
		# Update live priorities
		self.update_modules_priority(enabled_list, foreach_enabled)
		
		if self._loaded_modules == 0:
			self.ui.set_sensitive (True)
		
	def on_module_initialized(self, loader, modctx):
		self._inited_modules = self._inited_modules + 1
		if self._inited_modules == self._loaded_modules:
			self.ui.set_sensitive (True)
			get_deskbar_history().load(self.module_list)
							
	def on_applet_button_press(self, widget, event):
		# Left-Mouse-Button should focus the GtkEntry widget (for Fitt's Law
		# - so that a click on applet border on edge of screen activates the
		# most important widget).
		if event.button == 1:
			self.ui.receive_focus(event.time)
			return True
		
		# Middle click handling, we need this in the cuemiac
		if event.button == 2:
			self.middle_click = (event.x_root, event.y_root)
			
		return False
	
	def on_applet_button_release(self, widget, event):
		if event.button == 2:
			x, y = self.middle_click
			diffx, diffy = abs(x-event.x_root), abs(y-event.y_root)
			if diffx <= 3 and diffy <=3:
				self.ui.middle_click()
			
			self.middle_click = None
			
	def on_keybinding_button_press(self, widget, time):
		print 'Keybinding activated, focusing UI'
		self.ui.receive_focus(time)
		
	def on_history_item_selection (self, item, match, text):
		pass
			
	def on_keybinding_changed(self, binder, bound):
		# FIXME: provide visual clue when not bound
		# FIXME: should be used in the pref window
		pass

	def set_up_ui_signals (self):
		self.ui.connect ("match-selected", self.on_match_selected)
		self.ui.connect ("start-query", self.on_start_query)
		self.ui.connect ("stop-query", self.on_stop_query)
		self.ui.connect ("request-keybinding", self.on_request_keybinding)
		self.ui.connect ("keyboard-shortcut", self.on_keyboard_shortcut)
		self.applet.connect('change-orient', lambda applet, orient: self.ui.on_change_orient(applet))
		self.applet.connect('change-size', lambda applet, orient: self.ui.on_change_size(applet))

	def on_minchars_changed (self, value):
		if value is None or value.type != gconf.VALUE_INT:
			return
		self.minchars = value.get_int()
	
	def on_typingdelay_changed (self, value):
		if value is None or value.type != gconf.VALUE_INT:
			return
		self.typingdelay = value.get_int()

	def on_ui_changed (self, value):
		if value is None or value.type != gconf.VALUE_STRING:
			return
		
		ui_name = value.get_string()
		if ui_name == deskbar.WINDOW_UI_NAME:
			# You cannot switch to or from a window ui
			return

		self.ui.close_view()
		self.applet.remove (self.ui.get_view())
		#FIXME: Should we clean up signals and stuff on the old UI?

		if ui_name == deskbar.CUEMIAC_UI_NAME:
			self.ui = CuemiacButtonUI (self.applet, self.prefs)
		elif ui_name == deskbar.ENTRIAC_UI_NAME:
			self.ui = CuemiacEntryUI(self.applet, self.prefs)
		
		self.set_up_ui_signals ()
		self.applet.add (self.ui.get_view())
		self.applet.show_all ()
		self.ui.set_sensitive(True)
		print "Changing UI to:", value.get_string ()
