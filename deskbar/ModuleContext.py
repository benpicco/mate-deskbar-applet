class ModuleContext:
	"""A generic wrapper for any object stored in a ModuleList.
	"""	
	def __init__ (self, icon, enabled, module, filename, handler, infos):
		"""The icon should be a gtk.gdk.Pixbuf"""
		self.icon = icon
		self.enabled = enabled
		self.module = module
		self.filename = filename
		self.handler = handler
		self.infos = infos
