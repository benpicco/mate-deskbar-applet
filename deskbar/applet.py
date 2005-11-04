import os, time
# WARNING: Load gnome.ui before gnomeapplet or we have a nasty warning.
import gnome.ui
import gnomeapplet, gtk, gtk.gdk, gconf, gobject
from gettext import gettext as _

import deskbar, deskbar.deskbarentry, deskbar.about, deskbar.preferences, deskbar.applet_keybinder
from deskbar.module_list import ModuleLoader, ModuleList, ModuleLoader
from deskbar.preferences import update_modules_priority

class DeskbarApplet:
	def __init__(self, applet):
		self.applet = applet
		
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
		
		self.entry = deskbar.deskbarentry.DeskbarEntry(self.module_list)
		self.entry.get_evbox().connect("button-press-event", self.on_icon_button_press)
		self.entry.get_entry().connect("button-press-event", self.on_entry_button_press)
		self.loader.connect ("module-initialized", self.entry._connect_if_async)
		self.on_applet_sensivity_update(False)

		self.keybinder = deskbar.applet_keybinder.AppletKeybinder(self)

		# Set and retreive entry width from gconf
		self.config_width = deskbar.GCONF_CLIENT.get_int(deskbar.GCONF_WIDTH)
		if self.config_width == None:
			self.config_width = 20
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))
		self.config_expand = deskbar.GCONF_CLIENT.get_bool(deskbar.GCONF_EXPAND)
		if self.config_expand == None:
			self.config_expand = False
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_EXPAND, lambda x, y, z, a: self.on_config_expand(z.value))
				
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.applet.add(self.entry)
		self.applet.connect("button-press-event", self.on_applet_button_press)
		self.applet.connect('destroy', lambda x: self.keybinder.unbind())
		self.applet.connect('change-orient', lambda x, orient: self.sync_applet_size())
		self.applet.setup_menu_from_file (
			None, os.path.join(deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml"),
			None, [("About", self.on_about), ("Prefs", self.on_preferences)])

		self.applet.show_all()
		self.sync_applet_size()
		
		self.entry.get_entry().grab_focus()
		print 'GConf key:', applet.get_preferences_key()
		
	def on_about(self, component, verb):
		deskbar.about.show_about()
	
	def on_preferences(self, component, verb):
		deskbar.preferences.show_preferences(self.loader, self.module_list)

	def on_config_width(self, value=None):
		if value != None and value.type == gconf.VALUE_INT:
			self.config_width = value.get_int()
			self.sync_applet_size()
	
	def on_config_expand(self, value=None):
		if value != None and value.type == gconf.VALUE_BOOL:
			self.config_expand = value.get_bool()
			self.sync_applet_size()
	
	def sync_applet_size(self):
		if self.config_expand:
			self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR | gnomeapplet.EXPAND_MAJOR)
		else:
			self.applet.set_applet_flags(0)
			
			# Set the new size of the entry
			if self.applet.get_orient() == gnomeapplet.ORIENT_UP or self.applet.get_orient() == gnomeapplet.ORIENT_DOWN:
				self.entry.get_entry().set_width_chars(self.config_width)
			else:
				self.entry.get_entry().set_width_chars(-1)
				self.entry.queue_resize()
			
	
	def on_modules_loaded(self, loader):
		# Fetch the sorted handlers list from gconf
		enabled_list = deskbar.GCONF_CLIENT.get_list(deskbar.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING)
		
		def foreach_enabled(modctx):
			self.loader.initialize_module_async(	modctx)
			self._loaded_modules = self._loaded_modules + 1
		
		# Update live priorities
		update_modules_priority(self.module_list, enabled_list, foreach_enabled)
		# Update the model to reflect new order
		self.module_list.reorder_with_priority(enabled_list)
		
		if self._loaded_modules == 0:
			self.on_applet_sensivity_update(True)
		
	def on_module_initialized(self, loader, modctx):
		self._inited_modules = self._inited_modules + 1
		if self._inited_modules == self._loaded_modules:
			self.on_applet_sensivity_update(True)
		
	def on_applet_sensivity_update(self, active):
		self.entry.get_entry().set_sensitive(active)
		self.entry.get_evbox().set_sensitive(active)
		
	def on_applet_button_press(self, widget, event):
		if not self.entry.get_evbox().get_property('sensitive'):
			return False
			
		try:
			# GNOME 2.12
			self.applet.request_focus(long(event.time))
		except AttributeError:
			pass
			
		# Left-Mouse-Button should focus the GtkEntry widget (for Fitt's Law
		# - so that a click on applet border on edge of screen activates the
		# most important widget).
		if event.button == 1:
			self.entry.get_entry().select_region(0, -1)
			self.entry.get_entry().grab_focus()
			return True
		
		return False
	
	def on_icon_button_press(self, widget, event):
		if not self.entry.get_evbox().get_property('sensitive'):
			return False
			
		if event.button == 3:
			self.applet.emit("button-press-event", event)
			return True
		elif event.button == 1:
			self.build_history_menu(event)
			return True
		
		return False
		
	def on_entry_button_press(self, widget, event):
		try:
			# GNOME 2.12
			self.applet.request_focus(long(event.time))
		except AttributeError:
			pass
			
		return False

	def on_history_item_selection(self, item, match, text):
		match.action(text)
	
	def position_history_menu(self, menu):
		# Stolen from drivemount applet in gnome-applets/drivemount/drive-button.c:165
		align_to = self.entry.get_evbox()
		direction = self.entry.get_entry().get_direction()

		screen = menu.get_screen()
		monitor_num = screen.get_monitor_at_window(align_to.window)
		if monitor_num < 0:
			monitor_num = 0
		
		monitor = screen.get_monitor_geometry (monitor_num)
		menu.set_monitor (monitor_num)	
		
		tx, ty = align_to.window.get_origin()
		twidth, theight = menu.get_child_requisition()
		
		tx += align_to.allocation.x
		ty += align_to.allocation.y

		if direction == gtk.TEXT_DIR_RTL:
			tx += align_to.allocation.width - twidth

		if (ty + align_to.allocation.height + theight) <= monitor.y + monitor.height:
			ty += align_to.allocation.height
		elif (ty - theight) >= monitor.y:
			ty -= theight
		elif monitor.y + monitor.height - (ty + align_to.allocation.height) > ty:
			ty += align_to.allocation.height
		else:
			ty -= theight

		if tx < monitor.x:
			x = monitor.x
		elif tx > max(monitor.x, monitor.x + monitor.width - twidth):
			x = max(monitor.x, monitor.x + monitor.width - twidth)
		else:
			x = tx
		
		y = ty
		
		return (x, y, False)
		
	def build_history_menu(self, event):
		menu = gtk.Menu()
		
		history = self.entry.get_history()
		
		i = 0
		for text, match in history.get_all_history():
			# Recreate the action
			verbs = {"text" : text}
			verbs.update(match.get_name(text))
			verb = match.get_verb() % verbs
			
			# Retreive the icon
			icon = None
			handler = match.get_handler()
			if match.get_icon() != None:
				icon = match.get_icon()
			else:
				icon = handler.get_icon()
				
			label = gtk.Label()
			label.set_markup(verb)
			label.set_alignment(0.0, 0.0)
			
			image = gtk.Image()
			image.set_from_pixbuf(icon)
			
			box = gtk.HBox(False, 6)
			box.pack_start(image, expand=False)
			box.pack_start(label)
			
			item = gtk.MenuItem()
			item.add(box)		
			item.connect('activate', self.on_history_item_selection, match, text)
			menu.attach(item, 0, 1, i, i+1)
			i = i+1
		
		if i == 0:
			item = gtk.MenuItem(_("No History"))
			menu.attach(item, 0, 1, 0, 1)

		menu.show_all()
		menu.popup(None, None, self.position_history_menu, event.button, event.time)
