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
from deskbar.ui.cuemiac.CuemiacUIManager import CuemiacUIManager
from deskbar.ui.cuemiac.CuemiacLayoutProvider import CuemiacLayoutProvider
from deskbar.ui.cuemiac.LingeringSelectionWindow import LingeringSelectionWindow

class CuemiacButtonUI (DeskbarUI, CuemiacLayoutProvider):
	
	navigation_keys = [65364, 65362, 43, 45, 65293] # Down, Up, +, -, Enter
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		CuemiacLayoutProvider.__init__ (self)
		
		self.cuemiac = CuemiacUIManager (self) # Use self as CuemiacLayoutProvider
		
		## EXPERIMENTAL
		LingeringSelectionWindow (self.cuemiac.get_view())
			
		# Pass along signals from the cuemiac
		self.cuemiac.forward_deskbar_ui_signals (self)
				
		self.cbutton = CuemiacAppletButton (applet)
		self.cbutton.connect ("toggled-main", lambda x,y: self.update_popup_state())
		self.cbutton.connect ("toggled-arrow", lambda x,y: self.update_history_popup_state())

		self.scroll_view = gtk.ScrolledWindow ()
		self.scroll_view.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scroll_view.add (self.cuemiac.get_view())

		self.popup = CuemiacAlignedWindow (self.cbutton.button_main, applet)
		self.history_popup = CuemiacAlignedWindow (self.cbutton.button_arrow, applet)
		self.box = gtk.VBox ()
			
		self.popup.add (self.box)
		self.history_popup.add (self.cuemiac.get_history_view())

		# Add the view and entry to self.box		
		self.cuemiac.set_layout_by_orientation (applet.get_orient())
		
		self.box.connect ("size-request", lambda view, event: self.adjust_popup_size())
		self.cuemiac.get_history_view().connect ("key-press-event", self.on_history_key_press)
		self.cuemiac.get_entry().connect ("key-press-event", self.on_entry_key_press)
		
		
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
			# Unselect what we have in the entry, so we don't occupy the middle-click-clipboard
			# thus clearing the model on popup
			self.cuemiac.get_entry().select_region (0,0)
		
			# If the entry is empty or there's something in the middle-click-clipboard
			# clear the popup so that we can paste into the entry.
			if self.cuemiac.get_entry().get_text().strip() == "" or self.cuemiac.clipboard.wait_for_text():
				self.cuemiac.get_entry().set_text("")
				self.scroll_view.hide ()
				
			self.cbutton.button_arrow.set_active (False)
			self.adjust_popup_size ()
			# self.popup.update_position ()
			#self.update_entry_icon ()
			
			if time != None:
				self.popup.present_with_time (time)
			else:
				self.popup.present ()
			
			self.cuemiac.get_entry().grab_focus ()
		else:
			self.popup.hide ()
			self.emit ("stop-query")
	
	def receive_focus (self, time):
		# Toggle expandedness of the popup
		self.cbutton.button_main.set_active (not self.cbutton.button_main.get_active())
		# This will focus the entry since we are passing the real event time and not the toggling time
		self.update_popup_state (time)
		
	def update_history_popup_state (self):
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
		self.popup.show_all ()
	
	def append_matches (self, matches):
		self.cuemiac.append_matches (matches)
		self.popup.show_all()
	
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
			self.box.remove (self.cuemiac.get_entry())
			self.box.remove (self.scroll_view)
			should_reshow = True
		
		if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
			self.box.pack_start (self.cuemiac.get_entry(), False)
			self.box.pack_start (self.scroll_view)
		else:
			# We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
			self.box.pack_start (self.scroll_view)
			self.box.pack_start (self.cuemiac.get_entry(), False)
			
		self.cbutton.set_layout_by_orientation (orient)
		
		# Update icon according to direction
		self.on_change_size (self.applet)
		
		# Update how the popups is aligned
		self.popup.alignment = self.applet.get_orient ()
		self.history_popup.alignment = self.applet.get_orient ()
		
		if should_reshow :
			self.cuemiac.get_entry().show ()
			self.scroll_view.show ()
		
	def adjust_popup_size (self):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.cuemiac.get_view().size_request ()
		h = h + self.cuemiac.get_entry().allocation.height + 2 # To ensure we don't always show scrollbars
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
	
