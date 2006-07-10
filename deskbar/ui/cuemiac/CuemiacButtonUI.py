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
from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow
from deskbar.ui.cuemiac.CuemiacHistory import CuemiacHistoryPopup
from deskbar.DeskbarHistory import get_deskbar_history
from deskbar.ui.EntryHistoryManager import EntryHistoryManager
from deskbar.ui.cuemiac.CuemiacUIManager import CuemiacUIManager
from deskbar.ui.cuemiac.CuemiacLayoutProvider import CuemiacLayoutProvider
from deskbar.ui.cuemiac.CuemiacHeader import CuemiacHeader
from deskbar.ui.cuemiac.LingeringSelectionWindow import LingeringSelectionWindow

class CuemiacButtonUI (DeskbarUI, CuemiacLayoutProvider):
	
	navigation_keys = [65364, 65362, 43, 45, 65293] # Down, Up, +, -, Enter
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		self.clipboard = gtk.Clipboard (selection="PRIMARY")
		CuemiacLayoutProvider.__init__ (self)
		
		self.cuemiac = CuemiacUIManager (self) # Use self as CuemiacLayoutProvider
		
		LingeringSelectionWindow (self.cuemiac.get_view())
			
		# Pass along signals from the cuemiac
		self.cuemiac.forward_deskbar_ui_signals (self)
		
		self.cbutton = CuemiacAppletButton (applet)
		self.cbutton.connect ("toggled-main", lambda x,y: self.update_popup_state())
		self.cbutton.connect ("toggled-arrow", lambda x,y: self.update_history_popup_state())
		
		# We need an event time to focus the popup properly when it is shown
		self.cbutton.connect ("button-press-event", lambda widget, event: self.focus_popup(event.time))

		self.scroll_view = gtk.ScrolledWindow ()
		self.scroll_view.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scroll_view.add (self.cuemiac.get_view())

		self.last_focus_time = None # Used to store a ref to event.time for the last time we where focused
		self.popup = CuemiacAlignedWindow (self.cbutton.button_main, applet)#, gtk.WINDOW_POPUP)
		self.history_popup = CuemiacHistoryPopup (self.cbutton.button_arrow,
							applet,
							self.cuemiac.get_history_view ())
		self.box = gtk.VBox ()
		self.cuemiac_header = CuemiacHeader (self.cuemiac.get_entry())
			
		self.popup.add (self.box)
		self.history_popup.add (self.cuemiac.get_history_view())

		# Add the view and entry to self.box		
		self.cuemiac.set_layout_by_orientation (applet.get_orient())
		
		self.box.connect ("size-request", lambda view, event: self.adjust_popup_size())
		self.cuemiac.get_history_view().connect ("key-press-event", self.on_history_key_press)
		self.cuemiac.get_entry().connect ("key-press-event", self.on_entry_key_press)
		
		# We need to set the menu type hint on the popup window
		# or else it wont be aligned properly (see bug #335243).
		self.popup.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_MENU)
		
		self.screen_height = self.popup.get_screen().get_height ()
		self.screen_width = self.popup.get_screen().get_width ()
		self.max_window_height = int (0.8 * self.screen_height)
		self.max_window_width = int (0.6 * self.screen_width)
		
		self.set_sensitive (False)
		
		self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.applet.connect('change-background', self.on_change_background)
		#self.on_change_background()
	
		# Use same behavior for normal- and historic matches
		self.on_history_match_selected = self.on_match_selected
		
		self.box.show ()
		self.cuemiac_header.show_all ()
		self.cuemiac.get_entry().show ()
		self.cuemiac.get_view().show ()
		# don't show scroll_view just yet
		
	def on_change_background (self, widget, background, colour, pixmap):
		widgets = (self.applet, self.cbutton.button_main, self.cbutton.button_arrow)
		if background == gnomeapplet.NO_BACKGROUND or background == gnomeapplet.PIXMAP_BACKGROUND:
			for widget in widgets:
				copy = widget.get_style().copy()
				copy.bg_pixmap[gtk.STATE_NORMAL] = pixmap
				copy.bg_pixmap[gtk.STATE_INSENSITIVE]  = pixmap
				widget.set_style(copy)
		elif background == gnomeapplet.COLOR_BACKGROUND:
			for widget in widgets:
				widget.modify_bg(gtk.STATE_NORMAL, colour)

	def close_view(self):
		self.cbutton.button_arrow.set_active (False)
		self.cbutton.button_main.set_active (False)
		self.emit ("stop-query")
		
	def on_match_selected (self, cuemiac, match):
		# Close all popups
		self.cbutton.button_arrow.set_active (False)
		self.cbutton.button_main.set_active (False)
	
	def update_popup_state (self, time=None):
		if self.cbutton.get_active_main ():
			popup_was_visible = self.popup.get_property("visible")
			
			if not (popup_was_visible):
				# Don't risk that the window bounces around, thus
				# only recalc position when the popup isn't already shown
				self.popup.update_position ()
			
			# If the entry is empty or there's something in the middle-click-clipboard
			# clear the popup so that we can paste into the entry.
			if self.cuemiac.get_entry().get_text().strip() == "":
				self.cuemiac.get_entry().set_text("")
				self.scroll_view.hide ()
				
			self.cbutton.button_arrow.set_active (False)
			self.adjust_popup_size ()
			
			self.popup.stick() # Always show the popup
			self.popup.set_keep_above (True)
			
			self.popup.show ()
			if not time:
				time = self.last_focus_time
			self.focus_popup (time)			
			
			cursor_pos = self.cuemiac.get_entry().get_position()
			self.cuemiac.get_entry().grab_focus ()
			if popup_was_visible:
				# Reposition the cursor so we don't select the text,
				# allowing the user to type on
				self.cuemiac.get_entry().select_region (cursor_pos,cursor_pos)
			else:
				# We are popping up, so select all text
				self.cuemiac.get_entry().select_region (0,-1)
			
			# Clear our timestamp so metacity don't think we are pranksters,
			# if we try to reuse it
			self.last_focus_time = None
		else:
			self.popup.set_keep_above (False)
			self.popup.unstick()
			self.popup.hide ()
			self.emit ("stop-query")
		
		# Hide the history no matter what
		self.history_popup.popdown ()

	def focus_popup (self, time):
		if not self.popup.get_property ("visible"):
			return
		if time:
			self.popup.present_with_time (time)
		else:
			self.popup.present_with_time (gtk.get_current_event_time())
	
	def receive_focus (self, time):
		# Toggle expandedness of the popup
		self.last_focus_time = time
		self.cbutton.button_main.set_active (not self.cbutton.button_main.get_active())
		
		if not self.cbutton.button_main.get_active():
			self.emit ("stop-query")
		
	def update_history_popup_state (self):
		self.history_popup.popup ()
		self.popup.hide ()
		#if self.cbutton.get_active_arrow ():
		#	self.cbutton.button_main.set_active (False)
		#	self.history_popup.update_position ()
		#	self.history_popup.show_all ()
		#else:
		#	self.history_popup.popdown ()
	
	def get_view (self):
		return self.cbutton
		
	def set_sensitive (self, active):
		self.cbutton.set_sensitive (active)
		self.cbutton.button_main.set_sensitive (active)
		self.cbutton.button_arrow.set_sensitive (active)
		
	def on_change_orient (self, applet):
		# The cuemiac will call our own set_layout_by_orientation,
		# since we are the layout providers
		self.cuemiac.set_layout_by_orientation (applet.get_orient())
	
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
		
	def middle_click (self):
		text = self.clipboard.wait_for_text ()
		if text != None:
			self.cbutton.button_main.set_active (True)
			self.cuemiac.get_entry().grab_focus()
			self.cuemiac.get_entry().set_text(text)
			return True
	
	def on_matches_added (self, cuim):
		self.update_popup_state ()
		
	def append_matches (self, matches):
		self.cuemiac.append_matches (matches)
		self.scroll_view.show ()
	
	def on_stop (self, cuim):
		self.scroll_view.hide()
	
	def set_layout_by_orientation (self, cuim, orient):
		"""
		@param orient: Should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
		"""
		should_reshow = False
		
		if len (self.box.get_children()) > 0:
			# We have already added items to the box
			# ie. this is not the initial setup
			self.box.remove (self.cuemiac_header)
			self.box.remove (self.scroll_view)
			should_reshow = True
		
		if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
			self.box.pack_start (self.cuemiac_header, False)
			self.box.pack_start (self.scroll_view)
		else:
			# We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
			self.box.pack_start (self.scroll_view)
			self.box.pack_start (self.cuemiac_header, False)
			
		self.cbutton.set_layout_by_orientation (orient)
		
		# Update icon according to direction
		self.on_change_size (self.applet)
		
		# Update how the popups is aligned
		self.popup.alignment = self.applet.get_orient ()
		self.history_popup.alignment = self.applet.get_orient ()
		
		if should_reshow :
			self.cuemiac_header.show_all ()
			self.cuemiac.get_entry().show ()
			self.scroll_view.show ()
		
	def adjust_popup_size (self):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.cuemiac.get_view().size_request ()
		h = h + self.cuemiac_header.allocation.height + 2 # To ensure we don't always show scrollbars
		h = min (h, self.max_window_height)
		w = min (w, self.max_window_width)
		if w > 0 and h > 0:
			self.popup.resize (w, h)
					
	def on_history_key_press (self, history, event):
		if event.keyval == gtk.keysyms.Escape:
			self.cbutton.button_arrow.set_active (False)
	
	def on_entry_key_press (self, entry, event):
		if event.keyval == gtk.keysyms.Escape:
			self.cbutton.button_main.set_active (False)
				
gobject.type_register (CuemiacButtonUI)
	
