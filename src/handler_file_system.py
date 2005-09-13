import gnomevfs
import os
import os.path
import deskbar


def possible_completions(prefix):
	if len(prefix) == 0:
		return []
	
	head, tail = os.path.split(prefix)
	if len(head) == 0:
		return [tail]
	
	if not head.endswith("/"):
		head = head + "/"
	
	if len(tail) == 0:
		result = [head + f
			for f in os.listdir(os.path.expanduser(head))
			if not f.startswith(".")]
	else:
		result = [head + f
			for f in os.listdir(os.path.expanduser(head))
			if f.startswith(tail)]
	
	result.sort()
	return result
	


class Handler:
	def add_to_completions(self, text, completions, handler_icon, check_can_handle=True):
		if (not check_can_handle) or self.can_handle(text):
			name = self.name()
			files = possible_completions(text)
			for f in files:
				if os.path.isdir(f):
					word = "folder"
					image = deskbar.FOLDER_IMAGE
				else:
					word = "file"
					image = deskbar.FILE_IMAGE
				d = "Open the %s <b>%s</b>" % (word, deskbar.escape_markup(f))
				if f == os.path.expanduser(text):
					if handler_icon == None:
						handler_icon = image
						d = "<i>" + d + "</i>"
				completions.append([d, name, f, image.get_pixbuf()])
		return handler_icon


	def name(self):
		return "Handler_File_System"


	def can_handle(self, text):
		return text.startswith("/") or text.startswith("~")


	def handle(self, text, check_can_handle=True):
		text = os.path.expanduser(text)
		if gnomevfs.exists(text):
			deskbar.run_command("gnome-open \"%s\"", text)
