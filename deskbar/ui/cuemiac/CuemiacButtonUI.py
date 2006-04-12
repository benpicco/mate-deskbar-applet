from os.path import *
from gettext import gettext as _

import cgi
import sys

import gtk

import gnome, gobject, gconf
import gnomeapplet
import pango

import deskbar, deskbar.iconentry
from deskbar.ui import EntryHistoryManager
from deskbar.ui.DeskbarUI import DeskbarUI
from deskbar.ui.cuemiac.CuemiacAppletButton import CuemiacAppletButton
from deskbar.ui.cuemiac.CuemiacModel import CuemiacModel
from deskbar.ui.cuemiac.CuemiacTreeView import CuemiacTreeView
from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory, Nest
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow
from deskbar.ui.cuemiac.CuemiacHistory import CuemiacHistoryPopup
from deskbar.DeskbarHistory import get_deskbar_history
from deskbar.ui.EntryHistoryManager import EntryHistoryManager

class CuemiacButtonUI (DeskbarUI):
	
	navigation_keys = [65364, 65362, 43, 45, 65293] # Down, Up, +, -, Enter
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		
		self.default_entry_pixbuf = deskbar.Utils.load_icon("deskbar-applet-small.png", width=-1)
		self.clipboard = gtk.clipboard_get (selection="PRIMARY")
		
		self.cbutton = CuemiacAppletButton (applet)
		self.cbutton.connect ("toggled-main", lambda x,y: self.show_entry())
		self.cbutton.connect ("toggled-arrow", lambda x,y: self.show_history())

		self.popup = CuemiacAlignedWindow (self.cbutton.button_main, applet)
		self.icon_entry = deskbar.iconentry.IconEntry ()
		self.entry = self.icon_entry.get_entry ()
		self.entry_icon = gtk.Image ()
		self.history = get_deskbar_history ()
		self.history_popup = CuemiacHistoryPopup (self.cbutton.button_arrow, applet)
		self.model = CuemiacModel ()
		self.cview = CuemiacTreeView (self.model)
		self.scroll_win = gtk.ScrolledWindow ()
		self.scroll_win.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)	
		self.box = gtk.VBox ()
		
		self.set_layout_by_orientation (applet.get_orient(), reshow=False, setup=True)
			
		self.popup.add (self.box)
		self.scroll_win.add(self.cview)
		self.icon_entry.pack_widget (self.entry_icon, True)
		self.entry_icon.set_property('pixbuf', self.default_entry_pixbuf)
		
		self.popup.set_border_width (1)
		self.history_popup.set_border_width (1)
		
		self.box.connect ("size-request", lambda box, event: self.adjust_popup_size())
		on_entry_changed_id = self.entry.connect ("changed", self.on_entry_changed)
		
		# Connect first the history handler then the regular key handler
		self.history_entry_manager = EntryHistoryManager(self.entry, on_entry_changed_id)
		self.history_entry_manager.connect('history-set', self.on_history_set)
		
		self.entry.connect ("key-press-event", self.on_entry_key_press)
		self.entry.connect_after ("changed", lambda entry : self.update_entry_icon())
		self.entry.connect ("activate", self.on_entry_activate)
		self.cview.connect ("key-press-event", self.on_cview_key_press)
		self.cview.connect ("match-selected", self.on_match_selected)
		self.cview.connect_after ("cursor-changed", lambda treeview : self.update_entry_icon())
		self.history_popup.connect ("match-selected", self.on_match_selected, True)
		self.history_popup.connect ("key-press-event", self.on_history_key_press)		
		
		self.screen_height = self.popup.get_screen().get_height ()
		self.screen_width = self.popup.get_screen().get_width ()
		self.max_window_height = int (0.8 * self.screen_height)
		self.max_window_width = int (0.6 * self.screen_width)

		self.box.show ()
		self.icon_entry.show_all ()
		
		self.set_sensitive(False)		
		self.invalid = True
		
		self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.applet.connect('change-background', self.on_change_background)
		#self.on_change_background()
	
	def on_change_background (self, widget, background, colour, pixmap):
		widgets = (self.applet, self.cbutton.button_main, self.cbutton.button_arrow)
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
		self.cbutton.button_arrow.set_active (False)
		self.cbutton.button_main.set_active (False)
		self.emit ("stop-query")
		
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
		
	def on_match_selected (self, cview, match, is_historic=False):
		if match.__class__ == Nest or match.__class__ == CuemiacCategory:
			return
		self.emit ("match-selected", match[0], match[1])
		if is_historic :
			self.cbutton.button_arrow.set_active (False)
		else:
			self.cbutton.button_main.set_active (False)
	
	def show_entry (self, time=None):
		if self.cbutton.get_active_main ():
			# Unselect what we have in the entry, so we don't occupy the middle-click-clipboard
			# thus clearing the model on popup
			self.entry.select_region (0,0)
		
			# If the entry is empty or there's something in the middle-click-clipboard
			# clear the popup so that we can paste into the entry.
			if self.entry.get_text().strip() == "" or self.clipboard.wait_for_text():
				self.entry.set_text("")
				self.model.clear ()
				self.scroll_win.hide ()
				
			self.cbutton.button_arrow.set_active (False)
			self.adjust_popup_size ()
			# self.popup.update_position ()
			self.update_entry_icon ()
			
			if time != None:
				self.popup.present_with_time (time)
			else:
				self.popup.present ()
			
			self.entry.grab_focus ()
		else:
			self.popup.hide ()
			self.emit ("stop-query")
	
	def receive_focus (self, time):
		# Toggle expandedness of the popup
		self.cbutton.button_main.set_active(not self.cbutton.button_main.get_active())
		# This will focus the entry since we are passing the real event time and not the toggling time
		if self.cbutton.button_main.get_active():
			self.show_entry(time)
		
	def show_history (self):
		if self.cbutton.get_active_arrow ():
			self.cbutton.button_main.set_active (False)
			# self.history_popup.update_position ()
			self.history_popup.show_all ()
		else:
			self.history_popup.hide ()
	
	def get_view (self):
		return self.cbutton
		
	def set_sensitive (self, active):
		self.cbutton.set_sensitive (active)
		self.cbutton.button_main.set_sensitive (active)
		self.cbutton.button_arrow.set_sensitive (active)
		
	def on_change_orient (self, applet):
		self.set_layout_by_orientation (applet.get_orient())
	
	def on_change_size (self, applet):
		# FIXME: This is ugly, but i don't know how to get it right
		image_name = "deskbar-applet-panel"
		if applet.get_orient () in [gnomeapplet.ORIENT_UP, gnomeapplet.ORIENT_DOWN]:
			image_name += "-h"
		else:
			image_name += "-v"
		
		if applet.get_size() <= 36:
			image_name += ".png"
			s = -1
		else:
			image_name += ".svg"
			s = applet.get_size()-12
		
		self.cbutton.set_button_image_from_file (join(deskbar.ART_DATA_DIR, image_name), s)
	
	def append_matches (self, matches):
		if self.invalid :
			self.invalid = False
			self.model.clear()
			
		entry_text = self.entry.get_text().strip()
		for text, match in matches:
			self.model.append ((text, match))
		self.popup.show_all ()
		
	def middle_click(self):
		text = self.clipboard.wait_for_text ()
		if text != None:
			self.cbutton.button_main.set_active (True)
			self.entry.grab_focus()
			self.entry.set_text(text)
			return True
		
	def set_layout_by_orientation (self, orient, reshow=True, setup=False):
		"""orient should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
		reshow indicates whether or not the widget should call show() on all
		its children.
		setup should be true if this is the first time the widgets are laid out."""
		if not setup:
			self.box.remove (self.icon_entry)
			self.box.remove (self.scroll_win)
		
		if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
			self.box.pack_start (self.icon_entry, False)
			self.box.pack_start (self.scroll_win)
			self.cview.append_method = gtk.TreeStore.append
			self.cview.get_model().set_sort_order(gtk.SORT_DESCENDING)
			self.history.set_sort_order (gtk.SORT_DESCENDING)
		else:
			# We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
			self.box.pack_start (self.scroll_win)
			self.box.pack_start (self.icon_entry, False)
			self.cview.append_method = gtk.TreeStore.prepend
			self.cview.get_model().set_sort_order(gtk.SORT_ASCENDING)
			self.history.set_sort_order (gtk.SORT_ASCENDING)
			
		# Update icon accordingto direction
		self.on_change_size (self.applet)
		
		# Update the DeskbarAppletButton accordingly
		self.cbutton.set_orientation (orient, reshow)
		
		# Update how the popups is aligned
		self.popup.alignment = self.applet.get_orient ()
		self.history_popup.alignment = self.applet.get_orient ()
		
		if reshow:
			self.box.show_all ()
		
	def adjust_popup_size (self):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.cview.size_request ()
		h = h + self.icon_entry.allocation.height + 4 # To ensure we don't always show scrollbars
		h = min (h, self.max_window_height)
		w = min (w, self.max_window_width)
		if w > 0 and h > 0:
			self.popup.resize (w, h)
		
	def on_entry_changed (self, entry):
		self.history.reset()
		qstring = self.entry.get_text().strip()
		self.cview.set_query_string (qstring)
		if qstring == "":
			self.model.clear()
			self.scroll_win.hide ()
			self.emit ("stop-query")
			return
		
		self.invalid = True
		self.emit ("start-query", qstring)
	
	def hide_if_entry_empty (self):
		"""Checks if the entry is empty, and hides the window if so.
		Used by on_entry_changed() with a gobject.timeout_add()."""
		if self.entry.get_text().strip() == "":
			self.popup.hide ()
	
	def on_entry_key_press (self, entry, event):
		
		if event.keyval == gtk.keysyms.Escape:
			# bind Escape to clear the GtkEntry
			if not entry.get_text().strip() == "":
				# If we clear some text, tell async handlers to stop.
				self.emit ("stop-query")
			
			self.cbutton.set_active_main (False)
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
			if not self.cview.is_ready () : return
			self.cview.grab_focus ()
			last = self.cview.last_visible_path ()
			if last != None:
				self.cview.set_cursor (last)
			return True
			
		if event.keyval == 65364: # Down
			if not self.cview.is_ready () : return
			self.cview.grab_focus ()
			self.cview.set_cursor (self.model.get_path(self.model.get_iter_first()))
			return True

		return False
		
	def on_history_key_press (self, history, event):
		if event.keyval == gtk.keysyms.Escape:
			self.cbutton.button_arrow.set_active (False)
		self.update_entry_icon ()
			
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
			if self.applet.get_orient () in [gnomeapplet.ORIENT_DOWN, gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT]:
				# No selection, select top element # FIXME do this
				iter = self.model.get_iter_first()
				while iter != None and ((not self.model.iter_has_child(iter)) or (not self.cview.row_expanded(self.model.get_path(iter)))):
					iter = self.model.iter_next(iter)

				if iter != None:
					iter = self.model.iter_children(iter)

			else:
				# We are on a bottom panel - select the bottom element in the list 
				#FIXME: Should we iterate backwards up the list if the hit is a category?
				path = self.cview.last_visible_path()
				if path != None:
					iter = self.model.get_iter (self.cview.last_visible_path())
				
		if iter is None:
			return
			
		# FIXME check that selection is not cat or nest, and then activate			
		self.on_match_selected(widget, self.model[iter][self.model.MATCHES])


	def on_history_set(self, historymanager, set):
		if set:
			text, match = historymanager.current_history
			self.update_entry_icon (icon=match.get_icon())
		else:
			self.entry.set_text("")
			self.update_entry_icon ()
			
	def on_cview_key_press (self, cview, event):
		# If this is an ordinary keystroke just let the
		# entry handle it.
		if not event.keyval in self.navigation_keys:
			self.entry.event (event)
			return True
			
		path, column = cview.get_cursor ()
		model = cview.get_model ()
		if model.paths_equal (path, model.get_path(model.get_iter_first())):
			if event.keyval == 65362: # Up
				gobject.timeout_add (1, lambda : self.entry.grab_focus ())
			
		elif model.paths_equal (path, cview.last_visible_path()):
			if event.keyval == 65364: # Down
				gobject.timeout_add (1, lambda : self.entry.grab_focus ())

		return False		

gobject.type_register (CuemiacButtonUI)
