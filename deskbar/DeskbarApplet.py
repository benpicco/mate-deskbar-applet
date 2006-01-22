import os, time
from os.path import *
import gnomeapplet, gtk, gtk.gdk, gconf, gobject
from gettext import gettext as _

MAX_RESULTS_PER_HANDLER = 100


import deskbar, deskbar.ui
from deskbar.ModuleList import ModuleList
from deskbar.ModuleLoader import ModuleLoader
from deskbar.ui.DeskbarEntry import DeskbarEntry
from deskbar.ui.About import show_about
from deskbar.ui.DeskbarPreferencesUI import show_preferences
from deskbar.DeskbarAppletPreferences import DeskbarAppletPreferences
from deskbar.Keybinder import Keybinder
from deskbar.ui.cuemiac.Cuemiac import CuemiacUI
from deskbar.ui.completion.CompletionDeskbarUI import CompletionDeskbarUI

class DeskbarApplet:
	def __init__(self, applet):
		self.applet = applet
		
		self.start_query_id = 0
		
		self.ui = CompletionDeskbarUI (applet)
		self.ui.connect ("match-selected", self.on_match_selected)
		self.ui.connect ("start-query", self.on_start_query)
		self.ui.connect ("stop-query", self.on_stop_query)
		self.ui.connect ("request-keybinding", self.on_request_keybinding)
		self.ui.connect ("keyboard-shortcut", self.on_keyboard_shortcut)
		self.ui.connect ("request-history-show", self.on_request_history_show)
		self.ui.connect ("request-history-hide", self.on_request_history_hide)
		self.ui.set_sensitive (False)
		self.applet.add(self.ui.get_view ())
		self.applet.show_all()
		self.ui.get_view().queue_draw()
	
		self.prefs = DeskbarAppletPreferences(applet)
		
		self._inited_modules = 0
		self._loaded_modules = 0
		
		self.loader = ModuleLoader (deskbar.MODULES_DIRS)
		self.loader.connect ("modules-loaded", self.on_modules_loaded)
		self.loader.load_all_async()
		
		self.module_list = ModuleList ()
		self.loader.connect ("module-loaded", self.module_list.update_row_cb)
		self.loader.connect ("module-initialized", self.module_list.module_toggled_cb)
		self.loader.connect ("module-initialized", self.on_module_initialized)
		self.loader.connect ("module-not-initialized", self.on_module_initialized)
		self.loader.connect ("module-stopped", self.module_list.module_toggled_cb)
		self.loader.connect ("module-initialized", self._connect_if_async)
		
		self.keybinder = Keybinder(deskbar.GCONF_KEYBINDING)
		
		# Set and retreive enabled handler list from gconf
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_ENABLED_HANDLERS, lambda x, y, z, a: self.on_config_handlers(z.value))
		
		self.applet.connect("button-press-event", self.on_applet_button_press)
		self.applet.connect('destroy', lambda x: self.keybinder.unbind())
		self.applet.connect('change-orient', lambda x, orient: self.ui.on_change_orient(applet))
		self.applet.connect('change-size', lambda x, orient: self.ui.on_change_size(applet))
		self.applet.setup_menu_from_file (
			deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml",
			None, [("About", self.on_about), ("Prefs", self.on_preferences)])
			
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.ui.set_sensitive (True)
		
	def _connect_if_async (self, sender, context):
		if context.module.is_async():
			context.module.connect ('query-ready', lambda sender, qstring, matches: self.dispatch_matches([(qstring, match) for match in matches]))	
	
	def on_match_selected (self, match):
		print "match selected",match
	
	def on_start_query (self, sender, qstring, max_hits):
		if self.start_query_id != 0:
			gobject.source_remove(self.start_query_id)
			
		self.start_query_id = gobject.timeout_add(150, self.on_start_query_real, sender, qstring, max_hits)
		
	def on_start_query_real (self, sender, qstring, max_hits):
		print '-----------------------Start Query'
		results = []
		for modctx in self.module_list:
			if not modctx.enabled:
				continue
			if modctx.module.is_async():
				modctx.module.query_async(qstring, MAX_RESULTS_PER_HANDLER)
			else:
				matches = modctx.module.query(qstring, MAX_RESULTS_PER_HANDLER)
				for match in matches: # FIXME: This can be optimised
					results.append((qstring,match))
				
		self.ui.append_matches (results)
		
	def on_stop_query (self, sender=None):
		for modctx in self.module_list:
			if modctx.module.is_async():
				modctx.module.stop_query()
		
	def on_request_history_show (self, widget_to_align_to, alignment):
		print "history show request"
		
	def on_request_history_hide (self):
		print "history hide request"
		
	def on_request_keybinding (self, sender, match, keybinding):
		print "keybind request:", match, keybinding
		
	def on_keyboard_shortcut (self, sender, modifier, shortcut):
		print "shortcut triggered"
				
	def dispatch_matches (self, matches):
		self.ui.append_matches (matches)
	
	def on_about (self, component, verb):
		show_about()
	
	def on_preferences (self, component, verb):
		show_preferences(self, self.loader, self.module_list)
	
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
			self.on_applet_sensivity_update(True)
		
	def on_module_initialized(self, loader, modctx):
		self._inited_modules = self._inited_modules + 1
		if self._inited_modules == self._loaded_modules:
			self.ui.set_sensitive (True)
				
	def on_applet_button_press(self, widget, event):
		try:
			# GNOME 2.12
			self.applet.request_focus(long(event.time))
		except AttributeError:
			pass
			
		# Left-Mouse-Button should focus the GtkEntry widget (for Fitt's Law
		# - so that a click on applet border on edge of screen activates the
		# most important widget).
		if event.button == 1:
			self.ui.recieve_focus()
			return True
		
		return False

	def on_history_item_selection (self, item, match, text):
		pass
	
	def on_keybinding_activated(self, binder, time):
		# We want to grab focus here
		print 'Focusing the deskbar-applet entry'
		self.applet.request_focus(time)
		# Call receive focus
		
	def on_keybinding_changed(self, binder, bound):
		# FIXME: provide visual clue when not bound
		# FIXME: should be used in the pref window
		pass
