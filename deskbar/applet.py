import deskbar
import deskbar.config
import deskbar.handlers
import deskbar.iconentry
import gnomeapplet
import gobject
import gtk
import gtk.gdk


class DeskbarApplet:
	def __init__(self, applet):
		self.applet = applet
		self.gconf = deskbar.config.GConfBackend(applet.get_preferences_key())
		
		self.entry = None
		self.config_width_policy = "fixed"
		self.config_width = -1
		self.on_config_width()
		self.on_config_width_policy()
		self.gconf.notify_add("/width", self.on_config_width)
		self.gconf.notify_add("/width_policy", self.on_config_width_policy)
		
		self.construct_gui()


	def construct_gui(self):
		self.iconentry = deskbar.iconentry.IconEntry()

		entry = self.iconentry.get_entry()
		entry.connect("activate",           self.on_entry_activate)
		entry.connect("button-press-event", self.on_entry_button_press)
		entry.connect("changed",            self.on_entry_changed)
		entry.connect("key-press-event",    self.on_entry_key_press)
		entry.set_size_request(self.config_width, entry.size_request()[1])
		
		evbox = gtk.EventBox()
		evbox.set_property('visible-window', False)
		self.iconentry.image = gtk.Image()
		evbox.add(self.iconentry.image)
		# Icon clicks are passed through to the applet, so that we can
		# get both Fitt's Law goodness, and an Applet context menu (to
		# remove the applet, for example).
		evbox.connect("button-press-event", lambda box,event: self.applet.emit("button-press-event", event))
		self.iconentry.pack_widget(evbox, True)
		
		self.iconentry.image.set_property('pixbuf', deskbar.DESKBAR_IMAGE.get_pixbuf())
		
		self.construct_completions()
		
		width = self.gconf.get_int("/width", deskbar.DEFAULT_WIDTH)
		width_policy = self.gconf.get_string("/width_policy", "fixed")
		
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.applet.add(self.iconentry)
		self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
		self.applet.connect("button-press-event", self.on_applet_button_press)
	        self.applet.setup_menu_from_file (None, "Deskbar_Applet.xml", None,
	        	[("About", self.on_about), ("New", self.on_new), ("Prefs", self.on_preferences)])

		self.applet.show_all()
		entry.grab_focus()


	def construct_completions(self):
		# description, handler_name, handler_arg, pixbuf
		self.completionModel = gtk.ListStore(
			gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gtk.gdk.Pixbuf)
		completion = gtk.EntryCompletion()
		completion.set_popup_set_width(False)
		completion.set_match_func(lambda completion, key, it: True)
		completion.set_model(self.completionModel)
		completion.connect("match-selected", self.on_completion_selected)
		
		self.iconentry.get_entry().set_completion(completion)
		
		crp = gtk.CellRendererPixbuf()
		completion.pack_start(crp)
		completion.add_attribute(crp, "pixbuf", 3)
		
		crt = gtk.CellRendererText()
		completion.pack_start(crt)
		completion.add_attribute(crt, "markup", 0)
		completion.add_attribute(crt, "text", 0)
		completion.set_property("text-column", 0)
		completion.notify("text-column")


	def on_about(self, component, verb):
		import deskbar.about
		deskbar.about.show_about()


	def on_new(self, component, verb):
		import deskbar.preferences
		deskbar.preferences.show_preferences(self.gconf, True)


	def on_preferences(self, component, verb):
		import deskbar.preferences
		deskbar.preferences.show_preferences(self.gconf)


	def on_config_width(self):
		width = self.gconf.get_int("/width", deskbar.DEFAULT_WIDTH)
		
		if self.config_width == width:
			return
		self.config_width = width
		
		if self.entry != None:
			esr = self.iconentry.get_entry().size_request()
			self.iconentry.get_entry().set_size_request(width, esr[1])


	def on_config_width_policy(self):
		wp = self.gconf.get_string("/width_policy", "fixed")
		
		if self.config_width_policy == wp:
			return
		self.config_width_policy = wp
		
	        if wp == "maximal":
			self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR | gnomeapplet.EXPAND_MAJOR)
		else:
			self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)


	def on_completion_selected(self, completion, model, iterator):
		row = model[iterator]
		handler_name, handler_arg = row[1], row[2]
		
		# we wrap the set_text call in the gobject idle loop, otherwise
		# messing around with the completion and its iterator can
		# cause crashers.
		idle_callback = lambda entry: entry.set_text("")
		gobject.idle_add(idle_callback, self.iconentry.get_entry())
		
		deskbar.handlers.handle_with_specific_handler(handler_arg, handler_name)


	def on_entry_activate(self, widget):
		t = widget.get_text()
		widget.set_text("")
		deskbar.handlers.handle(t)


	def on_entry_changed(self, widget):
		self.completionModel.clear()
		deskbar.handlers.add_to_completions(widget.get_text(), self.completionModel, self.iconentry)

	def on_applet_button_press(self, widget, event):
		# Left-Mouse-Button should focus the GtkEntry widget (for Fitt's Law
		# - so that a click on applet border on edge of screen activates the
		# most important widget).
		if event.button == 1:
			self.iconentry.get_entry().select_region(0, -1)
			self.iconentry.get_entry().grab_focus()
			return True
		
		return False


	def on_entry_button_press(self, widget, event):
		if self.applet != None:
			self.applet.request_focus(long(event.time))
		return False


	def on_entry_key_press(self, entry, event):
		# bind Escape to clear the GtkEntry
		if event.keyval == gtk.keysyms.Escape:
			entry.set_text("")
		
		return False
