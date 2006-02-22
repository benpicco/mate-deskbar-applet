import gtk, gobject, gnomeapplet, gconf
from gettext import gettext as _

import deskbar
from deskbar.ui.DeskbarUI import DeskbarUI
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow
from deskbar.ui.cuemiac.Cuemiac import CuemiacModel
from deskbar.ui.cuemiac.Cuemiac import CuemiacTreeView
from deskbar.ui.cuemiac.Cuemiac import Nest
from deskbar.ui.cuemiac.Cuemiac import CuemiacCategory
from deskbar.ui.cuemiac.CuemiacHistory import CuemiacHistoryPopup
from deskbar.DeskbarHistory import get_deskbar_history
from deskbar.ui.EntryHistoryManager import EntryHistoryManager

class CuemiacEntryUI (DeskbarUI):
	
	navigation_keys = [65364, 65362, 43, 45, 65293] # Down, Up, +, -, Enter
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		
		self.default_entry_pixbuf = deskbar.Utils.load_icon("deskbar-applet-small.png", width=-1)
		self.clipboard = gtk.clipboard_get (selection="PRIMARY")

		self.icon_entry = deskbar.iconentry.IconEntry ()
		self.popup = CuemiacAlignedWindow (self.icon_entry, applet)
		self.entry = self.icon_entry.get_entry ()
		self.entry_icon = gtk.Image ()
		self.icon_event_box = gtk.EventBox ()
		self.history = get_deskbar_history ()
		self.history_popup = CuemiacHistoryPopup (self.entry_icon, applet)
		self.model = CuemiacModel ()
		self.cview = CuemiacTreeView (self.model)
		self.scroll_win = gtk.ScrolledWindow ()
		self.scroll_win.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)	
		
		self.set_layout_by_orientation (applet.get_orient())
			
		self.popup.add (self.scroll_win)
		self.scroll_win.add (self.cview)
		
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
		
		# Set up the event box for the entry icon
		self.icon_event_box.set_property('visible-window', False)
		self.icon_event_box.add(self.entry_icon)
		self.entry_icon.set_property('pixbuf', self.default_entry_pixbuf)
		self.icon_entry.pack_widget (self.icon_event_box, True)
		self.entry_icon.set_property('pixbuf', self.default_entry_pixbuf)
		
		self.popup.set_border_width (1)
		self.history_popup.set_border_width (1)
		
		self.scroll_win.connect ("size-request", lambda box, event: self.adjust_popup_size())
		on_entry_changed_id = self.entry.connect ("changed", self.on_entry_changed)
		
		# Connect first the history handler then the regular key handler
		self.history_entry_manager = EntryHistoryManager(self.entry, on_entry_changed_id)
		self.history_entry_manager.connect('history-set', self.on_history_set)
		self.icon_event_box.connect ("button-press-event", self.on_icon_button_press)
		
		self.entry.connect ("key-press-event", self.on_entry_key_press)
		self.entry.connect_after ("changed", lambda entry : self.update_entry_icon())
		self.entry.connect ("activate", self.on_entry_activate)
		self.entry.connect ("button-press-event", self.on_entry_button_press)
		self.cview.connect ("key-press-event", self.on_cview_key_press)
		self.cview.connect ("match-selected", self.on_match_selected)
		self.cview.connect_after ("cursor-changed", lambda treeview : self.update_entry_icon())
		self.history_popup.connect ("match-selected", self.on_match_selected, True)
		self.history_popup.connect ("key-press-event", self.on_history_key_press)		
		
		self.screen_height = self.popup.get_screen().get_height ()
		self.screen_width = self.popup.get_screen().get_width ()
		self.max_window_height = int (0.8 * self.screen_height)
		self.max_window_width = int (0.6 * self.screen_width)

		# Setup a bunch of window hiding conditions
		self.focus_out_from_cuemiac = False
		self.cview.connect ("focus-out-event", self.on_focus_out_event)
		self.entry.connect ("focus-out-event", self.on_focus_out_event)
		self.history_popup.connect ("focus-out-event", lambda *args: self.history_popup.hide())

		self.scroll_win.show_all ()
		self.icon_entry.show_all ()
		self.history_popup.get_child().show ()
		self.popup.set_focus_on_map (False)
		
		try:
			self.applet.set_background_widget(self.icon_entry)
		except Exception, msg:
			pass
		
		self.tooltips = gtk.Tooltips()
		#self.tooltips.set_tip(self.icon_event_box, _("Show previous actions"))
		
		self.invalid = True
		
		self.applet.set_flags(gtk.CAN_FOCUS)
	
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
				self.entry.set_width_chars(self.config_width)
			else:
				self.entry.set_width_chars(-1)
				self.icon_entry.queue_resize()
				
	def update_entry_icon (self, icon=None):
		if icon == None:
			icon = self.default_entry_pixbuf
			path, column = self.cview.get_cursor ()
		
			if path != None:
				item = self.model[self.model.get_iter(path)][self.model.MATCHES]
				if item.__class__ != CuemiacCategory and item.__class__ != Nest:
					text, match = item
					icon=match.get_icon()
				
		self.entry_icon.set_property('pixbuf', icon)
		self.entry_icon.set_size_request(deskbar.ICON_WIDTH, deskbar.ICON_HEIGHT)
	
	def show_popup (self, time=None):
		self.adjust_popup_size ()
		self.popup.update_position ()
		self.update_entry_icon ()
			
		if time:
			self.popup.present_with_time (time)
		elif not self.popup.get_property("visible"):
			self.popup.present_with_time (gtk.get_current_event_time())
			self.focus_out_from_cuemiac = True
	
	def hide_window (self, window, time=None):
		self.cview.get_selection().unselect_all ()
		self.history_popup.list_view.get_selection().unselect_all ()
		self.applet.request_focus(gtk.get_current_event_time())
		window.hide ()
		self.update_entry_icon ()
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
			
		self.entry.select_region(0, -1)
		self.entry.grab_focus()
	
	def get_view (self):
		return self.icon_entry
		
	def set_sensitive (self, active):
		self.icon_entry.set_sensitive (active)
		self.entry_icon.set_sensitive (active)
		self.icon_event_box.set_sensitive (active)
		
	def on_match_selected (self, cview, match, is_historic=False):
		if match.__class__ == Nest or match.__class__ == CuemiacCategory:
			return
		self.emit ("match-selected", match[0], match[1])
		if is_historic:
			self.hide_window (self.history_popup)
		else:
			self.hide_window (self.popup)
			self.entry.set_text ("")
		
	def on_change_orient (self, applet):
		self.set_layout_by_orientation (applet.get_orient())
	
	def on_change_size (self, applet):
		pass
	
	def append_matches (self, matches):
		if self.invalid :
			self.invalid = False
			self.model.clear()
			
		entry_text = self.entry.get_text().strip()
		#valid_matches = False
		#for text, match in matches:
		#	if text == entry_text: # FIXME: Maybe it will suffice to only check the first match
		#		self.model.append ((text,match))
		#		valid_matches = True
		#if valid_matches:
		#	self.popup.show_all ()
		for text, match in matches:
			self.model.append ((text, match))
		self.show_popup ()
		
	def middle_click(self):
		self.entry.grab_focus()
		
	def set_layout_by_orientation (self, orient):
		"""orient should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}."""
		if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
			self.cview.append_method = gtk.TreeStore.append
			self.cview.get_model().set_sort_order(gtk.SORT_DESCENDING)
		else:
			# We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
			self.cview.append_method = gtk.TreeStore.prepend
			self.cview.get_model().set_sort_order(gtk.SORT_ASCENDING)
		
		# Update how the popups is aligned
		self.popup.alignment = self.applet.get_orient ()
		self.history_popup.alignment = self.applet.get_orient ()
		
		# Update how the popups is aligned
		self.popup.alignment = self.applet.get_orient ()
		self.history_popup.alignment = self.applet.get_orient ()
		print "Layout changed to", self.applet.get_orient ()
		
	def adjust_popup_size (self):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.cview.size_request ()
		h = min (h, self.max_window_height) + 4
		w = min (w, self.max_window_width)
		if w > 0 and h > 0:
			self.popup.resize (w, h)
		
	def on_entry_changed (self, entry):
		self.history.reset()
		qstring = self.entry.get_text().strip()
		self.cview.set_query_string (qstring)
		if qstring == "":
			self.model.clear()
			self.hide_window (self.popup)
			self.emit ("stop-query")
			return
		
		self.invalid = True
		self.emit ("start-query", qstring)
	
	def on_entry_key_press (self, entry, event):
		
		if event.keyval == gtk.keysyms.Escape:
			# bind Escape to clear the GtkEntry
			self.model.clear ()
			self.entry.set_text ("")
			self.hide_window (self.popup, event.time)
			self.emit ("stop-query")
			return True
		
		if 	event.state&gtk.gdk.MOD1_MASK != 0:
			# Some Handlers want to know about Alt-keypress
			# combinations, for example.  Here, we notify such
			# Handlers.
			text = entry.get_text().strip()
			if text != "":
				self.emit('stop-query')
				self.emit('keyboard-shortcut', text, event.keyval)
			entry.set_text("")
			
			# Broadcast an escape
			event.state = 0
			event.keyval = gtk.keysyms.Escape
			entry.emit('key-press-event', event)
			return True
			
		if event.keyval == 65362: # Up
			self.focus_last_match (event.time)
			self.focus_out_from_cuemiac = True
			return True
			
		if event.keyval == 65364: # Down
			self.focus_first_match (event.time)
			self.focus_out_from_cuemiac = True
			return True

		return False
	
	def focus_last_match (self, timestamp):
		self.show_popup (timestamp)
		self.cview.grab_focus ()
		last = self.cview.last_visible_path ()
		self.cview.set_cursor (last)
	
	def focus_first_match (self, timestamp):
		self.show_popup (timestamp)
		self.cview.grab_focus ()
		self.cview.set_cursor (self.model.get_path(self.model.get_iter_first()))
	
	def on_history_key_press (self, history, event):
		if event.keyval == gtk.keysyms.Escape:
			self.hide_window (self.history_popup, event.time)
		self.update_entry_icon ()
	
	
	def on_history_set(self, historymanager, set):
		if set:
			text, match = historymanager.current_history
			self.update_entry_icon (icon=match.get_icon())
		else:
			self.entry.set_text("")
	
	def on_entry_activate(self, widget):
		# if we have an active history item, use it
		if self.history_entry_manager.current_history != None:
			text, match = self.history_entry_manager.current_history
			self.on_match_selected(widget, (text, match))
			return
			
		path, column = self.cview.get_cursor ()
		iter = None
		if path != None:
			iter = self.model.get_iter (path)
			
		if iter is None:
			# No selection, select top element # FIXME do this
			iter = self.model.get_iter_first()
			while (not self.model.iter_has_child(iter)) or (not self.cview.row_expanded(self.model.get_path(iter))):
				iter = self.model.iter_next(iter)
			iter = self.model.iter_children(iter)

		if iter is None:
			return
			
		# FIXME check that selection is not cat or nest, and then activate			
		self.on_match_selected(widget, self.model[iter][self.model.MATCHES])
		
	def on_focus_out_event(self, widget, event):
		if not self.focus_out_from_cuemiac:
			#self.hide_window(self.popup)
			self.popup.hide()
		else:
			self.focus_out_from_cuemiac = False
		
	def on_cview_key_press (self, cview, event):
		path, column = cview.get_cursor ()
		# If this is an ordinary keystroke, or there is no selection in the cview,
		#  just let the entry handle it.
		if not event.keyval in self.navigation_keys or path is None:
			self.entry.event (event)
			return True

		model = cview.get_model ()
		if model.paths_equal (path, model.get_path(model.get_iter_first())):
			if event.keyval == 65362: # Up
				self.cview.get_selection().unselect_all ()
				self.applet.request_focus (long(event.time))
				self.entry.grab_focus ()
				self.focus_out_from_cuemiac = True
				
		elif model.paths_equal (path, cview.last_visible_path()):
			if event.keyval == 65364: # Down
				self.cview.get_selection().unselect_all ()
				self.applet.request_focus (long(event.time))
				self.entry.grab_focus ()
				self.focus_out_from_cuemiac = True
				
		return False	
		
	def on_icon_button_press (self, widget, event):
		if not self.icon_event_box.get_property ('sensitive'):
			return False
			
		if event.button == 3:
			self.applet.emit ("button-press-event", event)
			return True
		elif event.button == 1:
			if self.history_popup.get_property('visible'):
				self.history_popup.hide()
				self.applet.request_focus(event.time)
			else:
				self.hide_window (self.popup, event.time)
				self.history_popup.show (event.time)
			return True
		
		return False	
		
	def on_entry_button_press(self, widget, event):
		try:
			# GNOME 2.12
			self.applet.request_focus(long(event.time))
		except AttributeError:
			pass
			
		return False

gobject.type_register (CuemiacEntryUI)
