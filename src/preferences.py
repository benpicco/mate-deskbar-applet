import deskbar
import deskbar.handlers
import gtk
import gtk.gdk
import gtk.glade
import gobject
import shutil
import urllib


def get_list_store_of_handlers():
	store = gtk.ListStore(str, gtk.gdk.Pixbuf, str, str, str)
	dh = deskbar.handlers.default_handler
	for h in deskbar.handlers.configurable_handlers:
		if h == dh:
			d = "•"
		else:
			d = ""
		store.append([d, h.image.get_pixbuf(), h.prefix, h.description, h.url_or_command])
	return store


def choose_icon_from_file():
	dialog = gtk.FileChooserDialog("Open Icon...",
		None,
		gtk.FILE_CHOOSER_ACTION_OPEN,
		(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
		gtk.STOCK_OPEN, gtk.RESPONSE_OK))
	dialog.set_default_response(gtk.RESPONSE_OK)

	f = gtk.FileFilter()
	f.set_name("Images")
	f.add_mime_type("image/ico")
	f.add_mime_type("image/png")
	f.add_mime_type("image/xpm")
	f.add_pattern("*.ico")
	f.add_pattern("*.png")
	f.add_pattern("*.xpm")
	dialog.add_filter(f)

	result = None
	response = dialog.run()
	if response == gtk.RESPONSE_OK:
		result = dialog.get_filename()
	dialog.destroy()
	return result


class PrefsDialog:
	def __init__(self, gconf, jump_to_new_engine = False):
		self.gconf = gconf
		self.store = get_list_store_of_handlers()
		self.is_dirty = False
		
		self.glade = gtk.glade.XML(deskbar.SHARED_DATA_DIR + "prefs-dialog.glade")
		self.dialog = self.glade.get_widget("preferences_dialog")
		
		w = self.gconf.get_int("/width", deskbar.DEFAULT_WIDTH)
		self.glade.get_widget("spin_width").set_value(w)
		
		width_policy = self.gconf.get_string("/width_policy", "fixed")
		if width_policy == "maximal":
			self.glade.get_widget("radio_max_width").set_active(True)
		else:
			self.glade.get_widget("radio_fixed_width").set_active(True)
		
		self.jump_to_new_engine = jump_to_new_engine
		if jump_to_new_engine:
			self.glade.get_widget("preferences_notebook").set_current_page(1)
		
		self.tree_view = self.glade.get_widget("engines_list")
		self.append_column(self.tree_view, "•",              0)
		self.append_column(self.tree_view, "Icon",           1)
		self.append_column(self.tree_view, "Abbreviation",   2)
		self.append_column(self.tree_view, "Description",    3)
		self.append_column(self.tree_view, "Command or URL", 4)
		
		self.tree_view.set_model(self.store)
		
		self.tree_view.get_selection().connect("changed", self.on_selection_changed)
		
		self.button_new = self.glade.get_widget("button_new")
		self.button_get_icon_from_website = self.glade.get_widget("button_get_icon_from_website")
		# other buttons are insensitive unless a row is selected
		self.buttons = []
		self.buttons.append(self.glade.get_widget("button_delete"))
		self.buttons.append(self.glade.get_widget("button_set_as_default"))
		self.buttons.append(self.glade.get_widget("button_choose_icon_from_file"))
		self.buttons.append(self.glade.get_widget("button_get_icon_from_website"))

		self.signal_autoconnect()
		self.notify_id_width = self.gconf.notify_add("/width", self.load_width)
		self.notify_id_width_policy = self.gconf.notify_add("/width_policy", self.load_width_policy)


	def write_store_to_disk(self):
		try:
			sorted = []
			f = file(deskbar.USER_DIR + "engines.txt", "w")
			def write(s):
				if len(s) == 0:
					f.write(".")
				else:
					f.write(s)
				f.write("\n")
			for i in range(len(self.store)):
				row = self.store[i]
				r = (row[2], row[3], row[4])
				if r != (".", ".", "."):
					sorted.append(r)
			sorted.sort()
			for r in sorted:
				write(r[0])
				write(r[1])
				write(r[2])
				f.write("\n")
			f.flush()
			f.close()
		except IOError:
			pass


	def append_column(self, widget, column_text, column_number):
		if column_number == 0:
			crt = gtk.CellRendererText()
			widget.append_column(gtk.TreeViewColumn(column_text, crt, text=column_number))
		elif column_number == 1:
			crp = gtk.CellRendererPixbuf()
			widget.append_column(gtk.TreeViewColumn(column_text, crp, pixbuf=column_number))
		else:
			crt = gtk.CellRendererText()
			crt.set_property("editable", True)
			crt.connect("edited", self.on_cell_edited, column_number)
			widget.append_column(gtk.TreeViewColumn(column_text, crt, text=column_number))


	def show_run_hide(self):
		self.dialog.show()
		if self.jump_to_new_engine:
			self.button_new.clicked()
		self.dialog.run()
		if self.is_dirty:
			self.write_store_to_disk()
			deskbar.handlers.load_handlers()
		self.dialog.hide()
		self.gconf.notify_remove(self.notify_id_width)
		self.gconf.notify_remove(self.notify_id_width_policy)


	def load_width(self):
		w = self.gconf.get_int("/width")
		spinner = self.glade.get_widget("spin_width")
		if w != spinner.get_value():
			spinner.set_value(w)


	def load_width_policy(self):
		if self.gconf.get_string("/width_policy") == "maximal":
			b = self.glade.get_widget("radio_max_width")
		else:
			b = self.glade.get_widget("radio_fixed_width")
		
		if not b.get_active():
			b.set_active(True)


	def signal_autoconnect(self):
		signals = {}
		for attr_name in dir(self):
			attr = getattr(self, attr_name)
			if callable(attr):
				signals[attr_name] = attr
		self.glade.signal_autoconnect(signals)


	def on_radio_max_width_toggled(self, radio):
		if radio.get_active():
			self.gconf.set_string("/width_policy", "maximal")


	def on_radio_fixed_width_toggled(self, radio):
		if radio.get_active():
			self.gconf.set_string("/width_policy", "fixed")


	def on_spin_width_value_changed(self, spinner):
		self.gconf.set_int("/width", spinner.get_value())


	def on_button_new_clicked(self, button):
		n = len(self.store)
		self.store.append(["", deskbar.GENERIC_IMAGE.get_pixbuf(), ".", ".", "."])
		self.tree_view.get_selection().select_path(n)
		self.tree_view.scroll_to_cell(n)
		self.is_dirty = True
		
		# we wrap the self.tree_view.set_cursor call in the gtk idle loop
		# for some unknown bug - see PyGTK FAQ 13.32
		foo = lambda view, path: view.set_cursor(path, view.get_column(1), True)
		gobject.idle_add(foo, self.tree_view, n)
	

	def on_button_delete_clicked(self, button):
		selection = self.tree_view.get_selection()
		model, selected = selection.get_selected()
		row = model.get_path(selected)[0]
		self.store.remove(self.store.get_iter(row))
		self.tree_view.columns_autosize()
		self.is_dirty = True


	def on_button_set_as_default_clicked(self, button):
		selection = self.tree_view.get_selection()
		model, selected = selection.get_selected()
		path = model.get_path(selected)
		abbreviation = self.store[path][2]
		if deskbar.handlers.default_handler and (abbreviation == deskbar.handlers.default_handler.prefix):
			return
		
		for i in range(len(self.store)):
			self.store[i][0] = ""
		self.store[path][0] = "•"
		
		deskbar.handlers.set_default_handler_by_prefix(abbreviation)
		try:
			f = file(deskbar.USER_DIR + "default-engine.txt", "w")
			f.write(abbreviation)
			f.flush()
			f.close()
		except IOError:
			pass


	def on_button_choose_icon_from_file_clicked(self, button):
		fn = choose_icon_from_file()
		if fn != None:
			try:
				extension = fn[fn.rindex("."):]
			except ValueError:
				extension = ""
			
			selection = self.tree_view.get_selection()
			model, selected = selection.get_selected()
			path = model.get_path(selected)
			abbreviation = self.store[path][2]
			shutil.copyfile(fn, deskbar.USER_DIR + deskbar.escape_dots(abbreviation) + extension)
			image = deskbar.load_image(abbreviation)
			self.store[path][1] = image.get_pixbuf()


	def on_button_get_icon_from_website_clicked(self, button):
		selection = self.tree_view.get_selection()
		model, selected = selection.get_selected()
		path = model.get_path(selected)
		url = self.store[path][4]
		if url.startswith("http://"):
			abbreviation = self.store[path][2]
			url = url[7:]
			n = url.find("/")
			if n != -1:
				url = url[:n]
			urllib.urlretrieve("http://" + url + "/favicon.ico",
				deskbar.USER_DIR + deskbar.escape_dots(abbreviation) + ".ico")
			image = deskbar.load_image(abbreviation)
			self.store[path][1] = image.get_pixbuf()


	def on_cell_edited(self, cell_renderer, path, new_text, column):
		new_text = new_text.replace("\n", " ")
		if self.store[path][column] != new_text:
			self.store[path][column] = new_text
			self.tree_view.columns_autosize()
			self.enable_button_get_icon_from_website()
			self.is_dirty = True


	def on_selection_changed(self, tree_selection):
		if tree_selection.count_selected_rows() == 0:
			for b in self.buttons:
				b.set_sensitive(False)
		else:
			for b in self.buttons:
				b.set_sensitive(True)
			
			self.enable_button_get_icon_from_website()
	
	
	def enable_button_get_icon_from_website(self):
		selection = self.tree_view.get_selection()
		model, selected = selection.get_selected()
		path = model.get_path(selected)
		self.button_get_icon_from_website.set_sensitive(
			self.store[path][4].startswith("http://"))


def show_preferences(gconf, jump_to_new_engine = False):
	PrefsDialog(gconf, jump_to_new_engine).show_run_hide()
