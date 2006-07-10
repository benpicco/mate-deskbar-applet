import gtk, gobject, gnomeapplet, gconf
from gettext import gettext as _

import deskbar
from deskbar.ui.DeskbarUI import DeskbarUI
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow
from deskbar.ui.cuemiac.CuemiacUIManager import CuemiacUIManager
from deskbar.ui.cuemiac.CuemiacLayoutProvider import CuemiacLayoutProvider
from deskbar.ui.cuemiac.CuemiacPopupEntry import CuemiacPopupEntry
from deskbar.ui.cuemiac.CuemiacHistory import CuemiacHistoryPopup
from deskbar.ui.cuemiac.LingeringSelectionWindow import LingeringSelectionWindow

class CuemiacEntryUI (DeskbarUI, CuemiacLayoutProvider):
	
	navigation_keys = [65364, 65362, 43, 45, 65293] # Down, Up, +, -, Enter
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		CuemiacLayoutProvider.__init__ (self)
		
		self.cuemiac = CuemiacUIManager (self) # Use self as layout provider
		self.entry = CuemiacPopupEntry (self.cuemiac.get_entry().entry, self.cuemiac.get_view(), applet) 
		self.cuemiac.forward_deskbar_ui_signals (self) # Let the manager handle the usual ui signals
		
		LingeringSelectionWindow (self.cuemiac.get_view())
				
		self.history_popup = CuemiacHistoryPopup (self.cuemiac.get_entry().get_image(),
							applet,
							self.cuemiac.get_history_view())
		
		#Gconf config
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
		
		self.cuemiac.get_entry().connect ("icon-clicked", self.on_icon_button_press)
		self.cuemiac.get_entry().connect ("button-press-event", self.on_entry_button_press)
		self.cuemiac.get_history_view().connect ("key-press-event", self.on_history_key_press)		
		self.entry.popup_window.connect ("hide", lambda widget: self.emit("stop-query"))
		self.cuemiac.get_entry().show ()
		self.cuemiac.get_history_view().show ()
		
		self.cuemiac.get_entry().set_icon_tooltip (_("Show previously used actions")) # FIXME: Translate
		
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.applet.connect('change-background', self.on_change_background)
	
		self.cuemiac.set_layout_by_orientation (applet.get_orient())
	
	def on_change_background (self, widget, background, colour, pixmap):
		# This does not work..
		widgets = (self.applet,)# self.icon_entry)
		if background == gnomeapplet.NO_BACKGROUND:
			pass
		elif background == gnomeapplet.COLOR_BACKGROUND:
			for widget in widgets:
				widget.modify_bg(gtk.STATE_NORMAL, colour)
		elif background == gnomeapplet.PIXMAP_BACKGROUND:
			for widget in widgets:
				copy = widget.get_style().copy()
				copy.bg_pixmap[gtk.STATE_NORMAL] = pixmap
				copy.bg_pixmap[gtk.STATE_INSENSITIVE]  = pixmap
				widget.set_style(copy)
	
	def close_view(self):
		self.entry.popdown ()
		self.history_popup.popdown()
		self.emit ("stop-query")
		
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
				self.cuemiac.get_entry().set_width_chars(self.config_width)
			else:
				self.cuemiac.get_entry().set_width_chars(-1)
				self.cuemiac.get_entry().queue_resize()
				
		print "Set entry width:", self.cuemiac.get_entry().get_width_chars()		
	
	def hide_window (self, window, time=None):
		self.cuemiac.unselect_all ()
		self.applet.request_focus(gtk.get_current_event_time())
		window.hide ()
		if time:
			self.receive_focus (time)
	
	def receive_focus (self, time):
		# Left-Mouse-Button should focus the GtkEntry widget (for Fitt's Law
		# - so that a click on applet border on edge of screen activates the
		# most important widget).
		try:
			# GNOME 2.12
			self.applet.request_focus(long(time))
		except AttributeError:
			pass
			
		self.cuemiac.get_entry().select_region(0, -1)
		self.cuemiac.get_entry().grab_focus()
	
	def get_view (self):
		return self.cuemiac.get_entry()
		
	def set_sensitive (self, active):
		self.cuemiac.get_entry().set_sensitive (active)
			
	def on_change_orient (self, applet):
		self.cuemiac.set_layout_by_orientation (applet.get_orient())
	
	def on_change_size (self, applet):
		pass
	
	def on_match_selected (self, cuim, match):
		self.entry.popdown ()
	
	def on_history_match_selected (self, cuim, match):
		print "cpeui hist match sel"
		self.history_popup.popdown ()
	
	def on_history_match_selected (self, cuim, match):
		self.history_popup.popdown()
	
	def on_matches_added (self, cuim):
		self.entry.popup ()
	
	def append_matches (self, matches):
		self.cuemiac.append_matches (matches)
		
	def middle_click(self):
		self.cuemiac.get_entry().grab_focus()
		
	def set_layout_by_orientation (self, cuim, orient):
		"""orient should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}."""
		# Update how the popups is aligned
		self.entry.set_layout_by_orientation (orient)
		self.history_popup.alignment = self.applet.get_orient ()
		
		print "Layout changed to", self.applet.get_orient ()
		
	def on_stop (self, cuim):
		self.entry.popdown ()
		self.history_popup.popdown()
		
	def on_icon_button_press (self, widget, event):
		if not self.cuemiac.get_entry().get_property ("sensitive"):
			return False
			
		elif event.button == 1:
			self.history_popup.popup ()
			return True
		
		# The underlying applet handles if event.button == 3.
		
		return False
		
	def on_entry_button_press (self, widget, event):
		try:
			# GNOME 2.12
			self.receive_focus (event.time)
		except AttributeError:
			pass
		return False

	def on_history_key_press (self, history, event):
		if event.keyval == gtk.keysyms.Escape:
			self.history_popup.popdown()

	def on_up_from_view_top (self, cuim, event):
		self.cuemiac.unselect_all ()
		self.receive_focus (event.time)
		
	def on_down_from_view_bottom (self, cuim, event):
		self.cuemiac.unselect_all ()
		self.receive_focus (event.time)


gobject.type_register (CuemiacEntryUI)
