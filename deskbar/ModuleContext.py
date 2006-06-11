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
		self.version = "0.0.0"
		if "version" in infos:
			self.version = infos["version"]
			
		self.update_infos = (False, None)

class WebModuleContext:
	"""A generic wrapper for any object stored in a WebModuleList.
		This represents a remote module available for download
	"""	
	def __init__ (self, id, name, description):
		self.id = id
		self.name = name
		self.description = description
		self.installing = False
