import gobject, gtk, gconf, gnomeapplet

import deskbar
from deskbar.ui.DeskbarUI import DeskbarUI
from deskbar.ui.completion.DeskbarEntry import DeskbarEntry
from deskbar.DeskbarHistory import get_deskbar_history

class CompletionDeskbarUI (DeskbarUI):
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		
		self.entry = DeskbarEntry(self)
		self.entry.get_evbox().connect("button-press-event", self.on_icon_button_press)
		self.entry.get_entry().connect("button-press-event", self.on_entry_button_press)
		
		# Set and retreive entry width from gconf
		self.config_width = deskbar.GCONF_CLIENT.get_int(self.prefs.GCONF_WIDTH)
		if self.config_width == None:
			self.config_width = 20
		deskbar.GCONF_CLIENT.notify_add(self.prefs.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))
		
		# Set and retreive expasoion settings
		self.config_expand = deskbar.GCONF_CLIENT.get_bool(self.prefs.GCONF_EXPAND)
		if self.config_expand == None:
			self.config_expand = False
		deskbar.GCONF_CLIENT.notify_add(self.prefs.GCONF_EXPAND, lambda x, y, z, a: self.on_config_expand(z.value))
		
		# Apply gconf values
		self.sync_applet_size()
		
		try:
			self.applet.set_background_widget(self.entry)
		except Exception, msg:
			print 'Could not set background widget, no transparency:', msg
		
		self.applet.set_flags(gtk.CAN_FOCUS)
		
	def set_sensitive(self, active):
		self.entry.get_entry().set_sensitive(active)
		self.entry.get_evbox().set_sensitive(active)
		
		# This queue_draw() is needed so that the Entry is drawn
		# properly right from the start, before it gets focus.  I don't
		# know if this is a bug with icon-entry or the theme, or whether
		# it's not a hack but just needed in general.  But here it is.
		self.entry.queue_draw()
	
	def on_icon_button_press(self, widget, event):
		if not self.entry.get_evbox().get_property('sensitive'):
			return False
			
		if event.button == 3:
			self.applet.emit("button-press-event", event)
			return True
		elif event.button == 1:
			self.popup_history(event)
			return True
		
		return False
	
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
			self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
			
			# Set the new size of the entry
			if self.applet.get_orient() == gnomeapplet.ORIENT_UP or self.applet.get_orient() == gnomeapplet.ORIENT_DOWN:
				self.entry.get_entry().set_width_chars(self.config_width)
			else:
				self.entry.get_entry().set_width_chars(-1)
				self.entry.queue_resize()
				
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
		
	def popup_history(self, event):
		menu = gtk.Menu()
		
		def on_match_selection(item, text, match):
			self.emit("match-selected", text, match)
			
		i = 0
		for text, match in get_deskbar_history().get_all_history():
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
			item.connect('activate', on_match_selection, text, match)
			menu.attach(item, 0, 1, i, i+1)
			i = i+1
		
		if i == 0:
			item = gtk.MenuItem(_("No History"))
			menu.attach(item, 0, 1, 0, 1)

		menu.show_all()
		menu.popup(None, None, self.position_history_menu, event.button, event.time)
		
	def on_entry_button_press(self, widget, event):
		try:
			# GNOME 2.12
			self.applet.request_focus(long(event.time))
		except AttributeError:
			pass
			
		return False
			
	def on_change_orient (self, applet):
		"""
		Connected to the applets "change-orient" signal.
		"""
		pass
	
	def on_change_size (self, applet):
		"""
		Connected to the applets "change-size" signal.
		"""
		pass
		
	def recieve_focus (self):
		"""
		Called when the applet recieves focus. Use fx. to pop up a text entry with focus.
		"""
			
		# Left-Mouse-Button should focus the GtkEntry widget (for Fitt's Law
		# - so that a click on applet border on edge of screen activates the
		# most important widget).
		self.entry.get_entry().select_region(0, -1)
		self.entry.get_entry().grab_focus()
	
	def append_matches (self, matches):
		if type(matches) != list:
			matches = [matches]
			
		self.entry.append_matches(matches)
		
	def get_view (self):
		"""
		Return the widget to be displayed for this UI.
		"""
		return self.entry


if gtk.pygtk_version < (2,8,0):
	gobject.type_register(CompletionDeskbarUI)
