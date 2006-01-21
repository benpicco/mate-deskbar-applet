import os, time
from os.path import *
import gnomeapplet, gtk, gtk.gdk, gconf, gobject
from gettext import gettext as _

import deskbar, deskbar.ui
from deskbar.ModuleList import ModuleList
from deskbar.ModuleLoader import ModuleLoader
from deskbar.ui.DeskbarEntry import DeskbarEntry
from deskbar.ui.About import show_about
from deskbar.ui.DeskbarPreferencesUI import show_preferences
from deskbar.DeskbarAppletPreferences import DeskbarAppletPreferences
from deskbar.Keybinder import Keybinder

class DeskbarApplet:
	def __init__(self, applet):
		self.applet = applet
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
		
		self.keybinder = Keybinder(deskbar.GCONF_KEYBINDING)
		self.keybinder.connect('activated', self.on_keybinding_activated)
		self.keybinder.connect('changed', self.on_keybinding_changed)
		self.keybinder.bind()

		# Set and retreive entry width from gconf
		self.config_width = deskbar.GCONF_CLIENT.get_int(self.prefs.GCONF_WIDTH)
		if self.config_width == None:
			self.config_width = 20
		deskbar.GCONF_CLIENT.notify_add(self.prefs.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))
		self.config_expand = deskbar.GCONF_CLIENT.get_bool(self.prefs.GCONF_EXPAND)
		if self.config_expand == None:
			self.config_expand = False
		deskbar.GCONF_CLIENT.notify_add(self.prefs.GCONF_EXPAND, lambda x, y, z, a: self.on_config_expand(z.value))
		
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_ENABLED_HANDLERS, lambda x, y, z, a: self.on_config_handlers(z.value))
		
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.applet.add(self.entry)
		self.applet.connect("button-press-event", self.on_applet_button_press)
		self.applet.connect('destroy', lambda x: self.keybinder.unbind())
		self.applet.connect('change-orient', lambda x, orient: self.sync_applet_size())
		self.applet.setup_menu_from_file (
			deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml",
			None, [("About", self.on_about), ("Prefs", self.on_preferences)])

		self.applet.show_all()
		self.sync_applet_size()
		
		self.entry.get_entry().grab_focus()
		
	def on_about(self, component, verb):
		show_about()
	
	def on_preferences(self, component, verb):
		show_preferences(self, self.loader, self.module_list)

	def on_config_width(self, value=None):
		if value != None and value.type == gconf.VALUE_INT:
			self.config_width = value.get_int()
			self.sync_applet_size()
	
	def on_config_expand(self, value=None):
		if value != None and value.type == gconf.VALUE_BOOL:
			self.config_expand = value.get_bool()
			self.sync_applet_size()
	
	def on_config_handlers(self, value):
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
			self.loader.initialize_module_async(	modctx)
			self._loaded_modules = self._loaded_modules + 1
		
		# Update live priorities
		self.update_modules_priority(enabled_list, foreach_enabled)
		
		if self._loaded_modules == 0:
			self.on_applet_sensivity_update(True)
		
	def on_module_initialized(self, loader, modctx):
		self._inited_modules = self._inited_modules + 1
		if self._inited_modules == self._loaded_modules:
			self.on_applet_sensivity_update(True)
	
	def on_applet_sensivity_update(self, active):
		# call set_sensitive
	
	def sync_applet_size(self):
		if self.config_expand:
			self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR | gnomeapplet.EXPAND_MAJOR)
		else:
			self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
			
			# Set the new size of the entry
			if self.applet.get_orient() == gnomeapplet.ORIENT_UP or self.applet.get_orient() == gnomeapplet.ORIENT_DOWN:
				self.entry.get_entry().set_width_chars(self.config_width)
			else:
				self.entry.get_entry().set_width_chars(-1)
				self.entry.queue_resize()
				
	def on_applet_button_press(self, widget, event):
		if not self.entry.get_evbox().get_property('sensitive'):
			return False
			
		try:
			# GNOME 2.12
			self.applet.request_focus(long(event.time))
		except AttributeError:
			pass
			
		# Call receive_focus

	
	def on_keybinding_activated(self, binder, time):
		# We want to grab focus here
		print 'Focusing the deskbar-applet entry'
		self.applet.request_focus(time)
		# Call receive focus
		
	def on_keybinding_changed(self, binder, bound):
		# FIXME: provide visual clue when not bound
		# FIXME: should be used in the pref window
		pass
