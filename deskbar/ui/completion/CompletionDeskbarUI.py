import gobject, gtk

from deskbar.ui.DeskbarUI import DeskbarUI
from deskbar.ui.completion import DeskbarEntry

class CompletionDeskbarUI (DeskbarUI):
	
	def __init__ (self, applet):
		DeskbarUI.__init__ (self, applet)
		
		self.entry = DeskbarEntry(self)
		self.entry.get_evbox().connect("button-press-event", self.on_icon_button_press)
		self.entry.get_entry().connect("button-press-event", self.on_entry_button_press)
		self.set_sensitive(False)
		
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
			self.emit('request-history-popup', self.entry.get_evbox(), self.entry.get_entry().get_direction())
			return True
		
		return False

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
