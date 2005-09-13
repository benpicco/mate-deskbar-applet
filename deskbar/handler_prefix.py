import deskbar


def as_command(url_or_command):
	if url_or_command.startswith("http://"):
		return "gnome-open \"" + url_or_command + "\""
	else:
		return url_or_command


class Handler:
	def __init__(self, prefix, description, url_or_command, image_name=None):
		self.prefix = prefix
		self.needs_whitespace_afterwards = (len(prefix) > 0) and (prefix[-1].isalnum())
		if image_name == None:
			image_name = prefix
		self.image = deskbar.load_image(image_name)
		
		# if the arg is optional, then url_or_command has the format
		# "no arg command|with arg command with %s", and description
		# is similarly two-part, split by the "|" character
		self.description = description
		bar = description.find("|")
		if bar == -1:
			self.with_arg_description = description
			self.sans_arg_description = None
		else:
			self.with_arg_description = description[bar+1:]
			self.sans_arg_description = description[:bar]
		
		self.url_or_command = url_or_command
		bar = url_or_command.find("|")
		if bar == -1:
			self.with_arg_command = as_command(url_or_command)
			self.sans_arg_command = None
		else:
			self.with_arg_command = as_command(url_or_command[bar+1:])
			self.sans_arg_command = as_command(url_or_command[:bar])
			if self.sans_arg_description == None:
				self.sans_arg_description = self.with_arg_description
		


	def add_to_completions(self, text, completions, handler_icon, check_can_handle=True):
		if (not check_can_handle) or self.can_handle(text):
			if check_can_handle:
				text = self.strip_prefix(text)

			if len(text) == 0:
				d = self.sans_arg_description
			else:
				d = self.with_arg_description.replace("%s", "<b>" + deskbar.escape_markup(text) + "</b>")

			if handler_icon == None:
				handler_icon = self.image
				d = "<i>" + d + "</i>"
			
			name = self.name()
			if not check_can_handle:
				name = deskbar.NO_CHECK_CAN_HANDLE + name
			
			completions.append([d, name, text, self.image.get_pixbuf()])
		return handler_icon


	def name(self):
		return "Handler_Prefix_" + self.prefix


	def strip_prefix(self, text):
		# strip the prefix, and then any leading/trailing whitespace
		return text[len(self.prefix):].strip()


	def can_handle(self, text, check_can_handle=True):
		if text == self.prefix:
			return self.sans_arg_command != None

		if self.needs_whitespace_afterwards:
			return text.startswith(self.prefix + " ")
		else:
			return text.startswith(self.prefix)


	def handle(self, text, check_can_handle=True):
		if check_can_handle and text.startswith(self.prefix):
			text = self.strip_prefix(text)

		if len(text) == 0:
			deskbar.run_command(self.sans_arg_command, text)
		else:
			deskbar.run_command(self.with_arg_command, text)
