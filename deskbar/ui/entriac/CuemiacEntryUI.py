import gtk, gobject, gnomeapplet, gconf
from gettext import gettext as _

import deskbar
from deskbar.ui.DeskbarUI import DeskbarUI
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow
from deskbar.ui.cuemiac.CuemiacUIManager import CuemiacUIManager
from deskbar.ui.cuemiac.CuemiacLayoutProvider import CuemiacLayoutProvider
from deskbar.ui.cuemiac.CuemiacPopupEntry import CuemiacPopupEntry
from deskbar.ui.cuemiac.LingeringSelectionWindow import LingeringSelectionWindow

class CuemiacEntryUI (DeskbarUI, CuemiacLayoutProvider):
	
	navigation_keys = [65364, 65362, 43, 45, 65293] # Down, Up, +, -, Enter
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		CuemiacLayoutProvider.__init__ (self)
		
		# This block is responsible for using the CuemiacPopupEntry for layout
		# Uncomment to use
		self.cuemiac = CuemiacUIManager ()
		self.entry = CuemiacPopupEntry (self.cuemiac.get_entry().entry, self.cuemiac.get_view(), applet)
		self.cuemiac.set_layout (self.entry)

		#self.cuemiac = CuemiacUIManager(self) # Use self as layout provider
		self.cuemiac.forward_deskbar_ui_signals (self) # Let the manager handle the usual ui signals
		
		LingeringSelectionWindow (self.cuemiac.get_view())
				
		# Create the popup windows for results and history
		self.popup = CuemiacAlignedWindow (self.cuemiac.get_entry(), applet)
		self.scroll_view = gtk.ScrolledWindow ()
		self.scroll_view.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scroll_view.add (self.cuemiac.get_view ())
		self.popup.add (self.scroll_view)
		
		self.history_popup = CuemiacAlignedWindow (self.cuemiac.get_entry().get_image(), applet)
		self.history_popup.add (self.cuemiac.get_history_view ())
		
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
		
		self.cuemiac.get_view().connect ("size-request", lambda box, event: self.adjust_popup_size())
		self.cuemiac.get_entry().connect ("icon-clicked", self.on_icon_button_press)
		self.cuemiac.get_entry().connect ("button-press-event", self.on_entry_button_press)
		self.cuemiac.get_history_view().connect ("key-press-event", self.on_history_key_press)		
		
		self.screen_height = self.popup.get_screen().get_height ()
		self.screen_width = self.popup.get_screen().get_width ()
		self.max_window_height = int (0.8 * self.screen_height)
		self.max_window_width = int (0.6 * self.screen_width)

		self.scroll_view.show_all ()
		self.cuemiac.get_entry().show ()
		self.cuemiac.get_history_view().show ()
		self.popup.set_focus_on_map (False)
		
		self.cuemiac.get_entry().set_icon_tooltip ("Show previous actions") # FIXME: Translate
		
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
		self.hide_window (self.popup)
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
		
	def focus_popup (self, time=None):
		self.adjust_popup_size ()
		self.popup.update_position ()
		
		if time:
			self.popup.present_with_time (time)
		elif not self.popup.get_property("visible"):
			self.popup.present_with_time (gtk.get_current_event_time())
			
	
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
	
	def on_match_selected (self, cview, match, is_historic=False):
		self.cuemiac.unselect_all()
		self.popup.hide()
		self.history_popup.hide()
	
	def on_matches_added (self, cuim):
		self.popup.show ()
	
	def append_matches (self, matches):
		self.cuemiac.append_matches (matches)
		
	def middle_click(self):
		self.cuemiac.get_entry().grab_focus()
		
	def set_layout_by_orientation (self, cuim, orient):
		"""orient should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}."""
		# Update how the popups is aligned
		self.popup.alignment = self.applet.get_orient ()
		self.history_popup.alignment = self.applet.get_orient ()
		
		print "Layout changed to", self.applet.get_orient ()
		
	def adjust_popup_size (self):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.cuemiac.get_view().size_request ()
		h = min (h, self.max_window_height) + 4
		w = min (w, self.max_window_width)
		if w > 0 and h > 0:
			self.popup.resize (w, h)
		
	def on_stop (self, cuim):
		self.hide_window (self.popup)
		self.hide_window (self.history_popup)
		
	def on_focus_loss (self, cuim, widget):
		self.popup.hide ()
		self.history_popup.hide ()
		
	def on_icon_button_press (self, widget, event):
		if not self.cuemiac.get_entry().get_property ("sensitive"):
			return False
			
		if event.button == 3:
			self.applet.emit ("button-press-event", event)
			return True
			
		elif event.button == 1:
			if self.history_popup.get_property('visible'):
				pass # The popup will be hidden by on_focus_loss
			else:
				self.hide_window (self.popup)
				self.history_popup.present_with_time (event.time)
			return True
		
		return False
		
	def on_entry_button_press(self, widget, event):
		try:
			# GNOME 2.12
			self.receive_focus (event.time)
		except AttributeError:
			pass
		return False

	def on_history_key_press (self, history, event):
		if event.keyval == gtk.keysyms.Escape:
			self.hide_window (self.history_popup)

	def on_up_from_view_top (self, cuim, event):
		self.receive_focus (event.time)
		
	def on_down_from_view_bottom (self, cuim, event):
		self.receive_focus (event.time)

	def on_up_from_entry (self, cuim, event):
		self.focus_popup (event.time)
		CuemiacLayoutProvider.on_up_from_entry (self, cuim, event) # Call super class method
		
	def on_down_from_entry (self, cuim, event):
		self.focus_popup (event.time)
		CuemiacLayoutProvider.on_down_from_entry (self, cuim, event) # Call super class method

gobject.type_register (CuemiacEntryUI)
