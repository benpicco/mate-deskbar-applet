import gobject

class CuemiacLayoutProvider :
	"""
	This abstract class is a part of the 'Cuemiac Duo' together
	with C{CuemiacUIManager}. These two classes is all you need
	to do a layout with the cuemiac.
	
	C{CuemiacLayoutProvider} is responsible for the layout and focus
	logic of a CuemiacUIManager.
	
	To avoid signal-setup-nightmare C{CuemiacUIManager} uses direct
	callbacks on the layout provider. You should think of this class
	as a template pattern in the ui manager, if you are familiar with
	design patterns.
	
	B{Important}
	To keep the classes coherent and ease debugging, please take care
	to only do layout anf focus stuff in the provided callbacks.
	
	B{Basic Usage}
	Subclass and overwrite the callbacks as you see fit. Some of the
	callbacks has a default behavior - if this is true, it will be
	described in the documentation for that method.
	
	The defaults will normally only work properly in a single window
	layout. If your layout includes several windows you might have luck
	with first calling C{gtk.Window.present_with_time(event.time)} and 
	then calling the default callback with 
	C{CuemiacLayoutProvider.on_foo(self, cuim)}.
	"""
	
	def __init__(self):
		pass
		
	def on_match_selected (self, cuim, match):
		"""
		Called when a match is selected by the user.
		@param cuim: C{CuemiacUIManager}
		@param match: C{deskbar.Match}
		"""
		pass
		
	def on_history_match_selected (self, cuim, match):
		"""
		Called when a match is selected from the history view
		by the user.
		@param cuim: C{CuemiacUIManager}
		@param match: C{deskbar.Match}
		"""
		pass
		
	def on_stop (self, cuim):
		"""
		Called when the ui manager emits a "stop-query" signal.
		This will typically hide the view, but there is no default behavior.
		@param cuim: C{CuemiacUIManager}
		"""
		pass
		
	def on_start_query (self, cuim, qstring):
		"""
		Called when the ui manager emits a "start-query" signal.
		@param cuim: C{CuemiacUIManager}
		@param qstring: The query string
		"""
		pass
			
	def on_matches_added (self, cuim):
		"""
		Called when matches are added to the view. The layout will
		typically call show() on the view or its parent window, but
		there is no default behavior.
		@param cuim: C{CuemiacUIManager}
		"""
		pass
		
	def on_up_from_history_top (self, cuim):
		"""
		The user hits the Up key, when the top match is selected in the
		history view.
		@param cuim: C{CuemiacUIManager}
		"""
		pass
		
	def on_down_from_history_bottom (self, cuim):
		"""
		The user hits the Down key, when the bottom match is selected in the
		history view.
		@param cuim: C{CuemiacUIManager}
		"""
		pass
		
	def on_up_from_view_top (self, cuim, event):
		"""
		The user hits the Up key, when the top match is selected in the
		normal match view.
		This defaults to focussing the entry.
		@param cuim: C{CuemiacUIManager}
		"""
		cuim.unselect_all ()
		gobject.timeout_add (10, lambda : cuim.get_entry().grab_focus() )
			
	def on_down_from_view_bottom (self, cuim, event):
		"""
		The user hits the Up key, when the bottom match is selected in the
		normal match view.
		This defaults to focussing the entry.
		@param cuim: C{CuemiacUIManager}
		"""
		cuim.unselect_all ()
		gobject.timeout_add (10, lambda : cuim.get_entry().grab_focus() )

	def on_up_from_entry (self, cuim, event):
		"""
		Called when the user hits the Up key when the entry is focussed.
		Only called when there are visible matches, else the ui manager
		will cycle the history.
		This defaults focussing the bottom match in the view.
		"""
		cuim.get_view().grab_focus ()
		cuim.get_view().focus_bottom_match ()
		
	def on_down_from_entry (self, cuim, event):
		"""
		Called when the user hits the Down key when the entry is focussed.
		Only called when there are visible matches, else the ui manager
		will cycle the history.
		This defaults focussing the top match in the view.
		"""
		cuim.get_view().grab_focus ()
		cuim.get_view().focus_top_match ()

	def on_focus_loss (self, cuim, widget):
		"""
		This method is called when one of the cuemiac widgets
		lose focus. Typically the layout would respond by hiding a popup
		window or such.
		
		This method is delayed a bit so that button presses outside
		the cuemiac scope is handled before this call. This is because
		a typical situation is one where the button in question is
		responsible for toggling window hide/show status. If on_focus_loss
		was not delayed a scenario would look like this:
		
		1) Click button - > Show window
		2) Click button again ->
		    2.1) Call on_focus_out(), hiding the window
		    2.2) Call on_button_press, toggling the window state (to show).
		
		Thus we end up showing, hiding and re-showing the window.
		
		Because of the delay, 2.1 and 2.2 are interchanged, thus making
		2.1 an obsolete window.hide() call (since the window is already hidden).
		    
		@param cuim: The C{CuemiacUIManager} responsible for the callback.
		@param widget: The widget loosing focus.
		"""
		pass
		
	def set_layout_by_orientation (self, cuim, orient):
		"""
		This method is automatically called by the cuemiac ui manager.
		Note that gnomeapplet.ORIENT_UP typically means that the ui
		is located at the I{bottom} of the screen (and vice versa for ORIENT_DOWN).
		@param cuim: The C{CuemiacUIManager} responsible for the callback.
		@param orient: One of gnomeapplet.ORIENT_{LEFT,RIGHT,UP,DOWN}.
		"""
		pass
