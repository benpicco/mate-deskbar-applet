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
		self.window_group = gtk.WindowGroup()
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
		self.selection.connect("changed", self.on_selection_changed)
		self.view.connect('button-press-event', self.on_view_button_press)
		self.view.connect('enter-notify-event', self.on_view_enter)
		self.view.connect('motion-notify-event', self.on_view_motion)
		self.view.connect ("size-request", lambda box, event: self.adjust_popup_size())
		#self.entry.connect("changed", self.on_entry_changed)
		self.entry.connect("key-press-event", self.on_entry_key_press)
		
		self.popup_window.connect('key-press-event', self.on_popup_key_press)		
		self.popup_window.connect('button-press-event', self.on_popup_button_press)
		
		# Screen constants
		self.screen_height = self.popup_window.get_screen().get_height ()
		self.screen_width = self.popup_window.get_screen().get_width ()
		self.max_window_height = int (0.8 * self.screen_height)
		self.max_window_width = int (0.6 * self.screen_width)

	def adjust_popup_size (self):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.view.size_request ()
		h = min (h, self.max_window_height) + 4
		w = min (w, self.max_window_width)
		if w > 0 and h > 0:
			self.popup_window.resize (w, h)

	def on_view_button_press (self, widget, event):
		print "CPE view button_press"
		path = self.view.get_path_at_pos(event.x, event.y)
		if path != None:
			# The match activation is handled by the UI manager
			return True
			
		return False
			
	def on_view_enter (self, widget, event):
		return self.ignore_enter
			
	def on_view_motion (self, widget, event):
		self.ignore_enter = False
		return False
			
	def on_selection_changed (self, selection):
		print "CPE sel cjhanged"
		if self.first_sel_changed:
			self.first_sel_changed = False
			if self.view.is_focus():
				self.selection.unselect_all()
			
	def on_matches_added (self, cuim):
		print 'Matches appended - popping up'
		self.popup()
	
	def on_stop (self, cuim):
		print "Stopped - popping down"
		self.popdown ()
	
	def set_layout_by_orientation (self, cuim, orient):
		pass # FIXME
	
	def on_down_from_entry (self, cuim, event):
		model, iter = self.selection.get_selected()
		
		if iter is None:
			# There is no selection - select the top match
			self.view.focus_top_match ()
			return
			
		elif model.paths_equal (model.get_path(iter), self.view.last_visible_path()):
			# We have the bottom match - select entry
			self.selection.unselect_all ()
			self.entry.select_region (0,-1)
			return
			
		# We have a normal move in the view, just move down
		next = model.iter_next (iter)
		print "next", next
		self.selection.select_iter (next)

		
	def on_up_from_entry (self, cuim, event):
		model, iter = self.selection.get_selected()
		print "CPE up from entry normal"		
		if iter is None:
			# There is no selection - select the bottom match
			self.view.focus_bottom_match ()
			return
			
		elif model.paths_equal (model.get_path(iter), model.get_path(model.get_iter_first())):
			# We have the top match - select entry
			self.selection.unselect_all ()
			self.entry.select_region (0,-1)
			return
			
		# We have a normal move in the view, move up
		parent = model.iter_parent (iter)
		self.selection.select_iter (parent)
		#self.view.grab_focus ()
		#self.view.event (event)
		#self.entry.grab_focus ()
		
	def on_match_selected (self, cuim, match):
		print "Match selected - popping down"
		self.popdown ()
	
	def on_entry_key_press (self, widget, event):			
		#if event.keyval in (gtk.keysyms.Up, gtk.keysyms.KP_Up,gtk.keysyms.Down, gtk.keysyms.KP_Down,gtk.keysyms.Page_Up,gtk.keysyms.Page_Down):
			#matches = 4
			#model, iter = self.selection.get_selected()
			#if iter == None:
			#	iter = model.get_iter_first()
			#if event.keyval in (gtk.keysyms.Up, gtk.keysyms.KP_Up):
			#	iter = model.iter_next(iter)
			#elif event.keyval in (gtk.keysyms.Down, gtk.keysyms.KP_Down):
			#	iter = model.iter_next(iter)
			#elif event.keyval in (gtk.keysyms.Page_Up):
			#	iter = model.iter_next(iter)
			#elif event.keyval in (gtk.keysyms.Page_Down):
			#	iter = model.iter_next(iter)
			
	#		if current_selected < 0:
	#			sel.unselect_all()
	#		elif current_selected < matches:
			#self.selection.unselect_all()
			#self.view.set_cursor(model.get_path(iter), None, False)
				#path = gtk.TreePath(index of selection)
				#tree_view.set_cursor(path, None, False)
			#print 'Move cursor in tree'
			#return True
			
		#elif event.keyval == gtk.keysyms.Escape:
		#	self.popdown()
		#	return True
			
		#elif event.keyval in (gtk.keysyms.Tab, gtk.keysyms.KP_Tab, gtk.keysyms.ISO_Left_Tab):
		#	self.popdown()
		#	#self.entry.get_toplevel().child_focus(gtk.DIR_TAB_FORWARD)
		#	return True
			
		#elif event.keyval in (gtk.keysyms.ISO_Enter, gtk.keysyms.KP_Enter, gtk.keysyms.Return):
		#	print 'Emit match selected'
		#	self.popdown()
		#	return True
		#
		print "CPE entry key press"
		return False
		# IDEA: PG_UP/DOWN could skip categories
	
	def popup (self):
		if (self.popup_window.flags()&gtk.MAPPED):
			return
		if not (self.entry.flags()&gtk.MAPPED):
			return
		if not (self.entry.flags()&gtk.HAS_FOCUS):
			return
		self.ignore_enter = True
		
		entry_toplevel = self.entry.get_toplevel()
		entry_group = self.window_group
		if entry_toplevel != None and entry_toplevel.group != None:
			entry_group = entry_toplevel.group
		entry_group.add_window (self.popup_window)

		self.view.grab_focus()
		self.view.realize()
		self.selection.unselect_all()
		
		self.popup_window.update_position()
		self.popup_window.show_all ()

		# Grab pointer
		self.popup_window.grab_add()
		gtk.gdk.pointer_grab(
			self.popup_window.window, True,
			gtk.gdk.BUTTON_PRESS_MASK|
				gtk.gdk.BUTTON_RELEASE_MASK|
				gtk.gdk.POINTER_MOTION_MASK,
			None, None, gtk.get_current_event_time())
	
	def popdown (self):
		if not (self.popup_window.flags()&gtk.MAPPED):
			return
		
		self.ignore_enter = False

		self.popup_window.hide ()		

		# Ungrab pointer
		gtk.gdk.pointer_ungrab(gtk.get_current_event_time())
		self.popup_window.grab_remove()
	
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
		print "CPE popup b_p"
		if not (self.popup_window.flags()&gtk.MAPPED):
			return False
			
		self.popdown()
		return True

