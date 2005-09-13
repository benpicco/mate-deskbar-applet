import deskbar


class Handler:
	def add_to_completions(self, text, completions, handler_icon, check_can_handle=True):
		if (not check_can_handle) or self.can_handle(text):
			name = self.name()
			if text.find("/") == -1:
				text = text + "/"
			if not text.startswith("http://"):
				text = "http://" + text
			d = "Open the website <b>%s</b>" % deskbar.escape_markup(text)
			if handler_icon == None:
				handler_icon = deskbar.WEB_IMAGE
				d = "<i>" + d + "</i>"
			completions.append([d, name, text, deskbar.WEB_IMAGE.get_pixbuf()])
		return handler_icon


	def name(self):
		return "Handler_Web_Site"


	def can_handle(self, text):
		if len(text) == 0:
			return False
		
		if text.find(" ") != -1:
			return False
			
		return (text.find(".") != -1) and (not text.endswith(".")) and (not text.startswith("."))


	def handle(self, text, check_can_handle=True):
		if text.find("/") == -1:
			text = text + "/"
		if not text.startswith("http://"):
			text = "http://" + text
		deskbar.run_command("gnome-open \"%s\"", text)
