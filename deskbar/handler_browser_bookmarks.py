import gconf
import deskbar


bookmarks_index = deskbar.indexer.Index()


def load_browser_bookmarks():
	bookmarks_index.clear()
	h = gconf.client_get_default().get_string("/desktop/gnome/url-handlers/http/command")
	if h.find("firefox") != -1:
		import deskbar.browser_bookmarks_mozilla
		deskbar.browser_bookmarks_mozilla.add_to_index(bookmarks_index, "firefox")
	elif h.startswith("mozilla"):
		import deskbar.browser_bookmarks_mozilla
		deskbar.browser_bookmarks_mozilla.add_to_index(bookmarks_index, "mozilla")
	elif h.startswith("epiphany"):
		import deskbar.browser_bookmarks_epiphany
		deskbar.browser_bookmarks_epiphany.add_to_index(bookmarks_index)
	


class Handler:
	def add_to_completions(self, text, completions, handler_icon, check_can_handle=True):
		name = self.name()
		for (title, href) in bookmarks_index.look_up(text):
			d = "Open the bookmark <b>%s</b> (%s)" % \
				(deskbar.escape_markup(title),
				deskbar.escape_markup(deskbar.ellipsize(href)))
			completions.append([d, name, href, deskbar.WEB_BOOKMARK_IMAGE.get_pixbuf()])
		return handler_icon


	def name(self):
		return "Handler_Browser_Bookmarks"


	def can_handle(self, text):
		False


	def handle(self, text, check_can_handle=True):
		deskbar.run_command("gnome-open \"%s\"", text)


load_browser_bookmarks()
