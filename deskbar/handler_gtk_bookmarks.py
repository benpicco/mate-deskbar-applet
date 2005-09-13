import gnomevfs
import os.path
import deskbar
import deskbar.indexer


bookmarks_index = deskbar.indexer.Index()


def load_gtk_bookmarks():
	bookmarks_index.clear()
	try:
		sorted_lines = []
		for line in file(os.path.join(deskbar.HOME_DIR, "/.gtk-bookmarks")):
			line = line.replace("%20", " ").strip()
			if gnomevfs.exists(line):
				if line.startswith("file://"):
					line = line[7:]
				if line.startswith(deskbar.HOME_DIR):
					line = "~" + line[len(deskbar.HOME_DIR):]
				sorted_lines.append(line)
		sorted_lines.sort()
		for path in sorted_lines:
			head, tail = os.path.split(path)
			bookmarks_index.add(tail, (path, tail))
	except IOError:
		pass


class Handler:
	def add_to_completions(self, text, completions, handler_icon, check_can_handle=True):
		name = self.name()
		for (path, tail) in bookmarks_index.look_up(text):
			d = "Open the bookmark <b>%s</b> (%s)" % \
				(deskbar.escape_markup(tail), deskbar.escape_markup(path))
			completions.append([d, name, path, deskbar.FOLDER_BOOKMARK_IMAGE.get_pixbuf()])
		return handler_icon


	def name(self):
		return "Handler_Gtk_Bookmarks"


	def can_handle(self, text):
		return False


	def handle(self, text, check_can_handle=True):
		deskbar.run_command("gnome-open \"%s\"", text)


load_gtk_bookmarks()
