import gtk, gtk.gdk, gtk.keysyms, gobject

from deskbar.ui.cuemiac.CuemiacLayoutProvider import CuemiacLayoutProvider
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow

class CuemiacPopupEntry (CuemiacLayoutProvider, gtk.HBox):

	def __init__(self, entry, view, applet):
		"""
		@param entry: A C{gtk.Entry}, C{CuemiacEntry} or compatible widget
		@param treeview: A {CuemiacTreeView}
		"""
		CuemiacLayoutProvider.__init__ (self)
		gtk.HBox.__init__(self)
		
		self.entry = entry
		self.view = view
		
		# State variables
		self.ignore_enter = False		
		self.first_sel_changed = True
		
		# Our own UI elements
		self.view = view		
		self.view.set_hover_selection (True)
		self.selection = self.view.get_selection()
		self.window_group = None
		self.popup_window = CuemiacAlignedWindow (self.entry, applet, gtk.WINDOW_POPUP)
		self.scroll_view = gtk.ScrolledWindow ()
		
		# Set up popup
		self.scroll_view.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scroll_view.add (self.view)
		self.popup_window.add (self.scroll_view)
		
		# Tweak selection		
		self.selection.set_mode(gtk.SELECTION_SINGLE)
		self.selection.unselect_all()
		
		# Signals setup
		self.view.connect('button-press-event', self.on_view_button_press)
		self.view.connect('enter-notify-event', self.on_view_enter)
		self.view.connect('motion-notify-event', self.on_view_motion)
		self.view.connect ("size-request", lambda box, event: self.adjust_popup_size())
		self.entry.connect("key-press-event", self.on_entry_key_press)
		
		self.popup_window.connect('key-press-event', self.on_popup_key_press)		
		self.popup_window.connect('button-press-event', self.on_popup_button_press)
		
		self.popup_window.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_MENU)
		
		# Screen constants
		self.screen_height = self.popup_window.get_screen().get_height ()
		self.screen_width = self.popup_window.get_screen().get_width ()
		self.max_window_height = int (0.8 * self.screen_height)
		self.max_window_width = int (0.6 * self.screen_width)

	def set_layout_by_orientation (self, orient):
		self.popup_window.alignment = orient

	def adjust_popup_size (self):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.view.size_request ()
		h = min (h, self.max_window_height) + 4
		w = min (w, self.max_window_width)
		if w > 0 and h > 0:
			self.popup_window.resize (w, h)

	def on_view_button_press (self, widget, event):
		if self.view.coord_is_category (event.x, event.y):
			# Don't popdown, we just expanded or collapsed a row
			return False
		else:
			self.popdown()
			return True
	
	def on_view_enter (self, widget, event):
		return self.ignore_enter
			
	def on_view_motion (self, widget, event):
		self.ignore_enter = False
		return False
			
	def on_entry_key_press (self, widget, event):			
		return False
		# IDEA: PG_UP/DOWN could skip categories
	
	def popup (self):
		if (self.popup_window.flags()&gtk.MAPPED):
			return
		if not (self.entry.flags()&gtk.MAPPED):
			return
		if not (self.entry.flags()&gtk.HAS_FOCUS):
			self.selection.unselect_all()
			return
		self.ignore_enter = True
		
		if not self.window_group :
			entry_toplevel = self.entry.get_toplevel()
			if entry_toplevel != None and entry_toplevel.group != None:
				entry_toplevel.group.add_window (self.popup_window)
				self.window_group = entry_toplevel.group
			elif entry_toplevel is not None:
				self.window_group = gtk.WindowGroup ()
				self.window_group.add_window (entry_toplevel)
				self.window_group.add_window (self.popup_window)
			else:
				print "WARNING in CuemiacEntryPopup : No toplevel window for entry!"
				return
					
		self.popup_window.update_position()
		self.popup_window.show_all ()
		self.view.grab_focus()

		# Grab pointer
		self.view.grab_add()
		gtk.gdk.pointer_grab(
			self.view.window, True,
			gtk.gdk.BUTTON_PRESS_MASK|
				gtk.gdk.BUTTON_RELEASE_MASK|
				gtk.gdk.POINTER_MOTION_MASK,
			None, None, gtk.get_current_event_time())
			
		self.selection.unselect_all() # We need to do this again after showing
			
	def popdown (self):
		if not (self.popup_window.flags()&gtk.MAPPED):
			return
		
		self.ignore_enter = False

		self.popup_window.hide ()		

		# Ungrab pointer
		gtk.gdk.pointer_ungrab(gtk.get_current_event_time())
		self.view.grab_remove()
	
	def on_popup_key_press(self, widget, event):
		if not (self.popup_window.flags()&gtk.MAPPED):
			return False
		model, iter = self.selection.get_selected ()
		if iter is None:
			# We are in the entry
			self.entry.event (event)
		else:
			# We are in the view
			self.view.event (event)
		return True
		
	def on_popup_button_press(self, widget, event):
		if not (self.popup_window.flags()&gtk.MAPPED):
			return False
			
		self.popdown()
		return True

