import gconf


# This is a back-end for when running the applet in a stand-alone window, so
# it does not have an applet-specific gconf-key given to it by the panel.
class GConfMockClient:
	def __init__(self):
		self.values = {}
		self.callbacks_by_key = {}
		self.callbacks_by_id = {}
		self.keys_by_id = {}
		self.next_notify_id = 0


	def get_int(self, key):
		if self.values.has_key(key):
			return int(self.values[key])
		else:
			return 0


	def get_string(self, key):
		if self.values.has_key(key):
			return str(self.values[key])
		else:
			return None


	def set_int(self, key, value):
		self.set(key, value)

	
	def set_string(self, key, value):
		self.set(key, value)


	def set(self, key, value):
		self.values[key] = value
		if self.callbacks_by_key.has_key(key):
			for cb in self.callbacks_by_key[key]:
				cb.__call__(None, None, None, None)

	
	def notify_add(self, key, callback):
		if self.callbacks_by_key.has_key(key):
			self.callbacks_by_key[key].append(callback)
		else:
			self.callbacks_by_key[key] = [callback]
		
		self.callbacks_by_id[self.next_notify_id] = callback
		self.keys_by_id[self.next_notify_id] = key
		
		self.next_notify_id += 1
		return self.next_notify_id - 1


	def notify_remove(self, callback_id):
		key = self.keys_by_id.pop(callback_id)
		cb = self.callbacks_by_id.pop(callback_id)
		self.callbacks_by_key[key].remove(cb)


#-------------------------------------------------------------------------------

class GConfBackend:
	def __init__(self, prefix):
		if prefix == None:
			self.prefix = ""
			self.client = GConfMockClient()
		else:
			self.prefix = prefix
			self.client = gconf.client_get_default()
		
		self.notify_ids = []

	
	def get_int(self, key, default_value=None):
		x = self.client.get_int(self.prefix + key)
		if x == 0:
			return default_value
		else:
			return x


	def get_string(self, key, default_value=None):
		x = self.client.get_string(self.prefix + key)
		if x == None:
			return default_value
		else:
			return x

	def set_int(self, key, value):
		self.client.set_int(self.prefix + key, int(value))


	def set_string(self, key, value):
		self.client.set_string(self.prefix + key, str(value))


	def notify_add(self, key, callback):
		cb = lambda client, connection_id, entry, args: callback()
		n = self.client.notify_add(self.prefix + key, cb)
		self.notify_ids.append(n)
		return n


	def notify_remove(self, notify_id):
		self.client.notify_remove(notify_id)
		self.notify_ids.remove(notify_id)


	def destroy(self):
		for n in self.notify_ids:
			self.client.notify_remove(n)
		# clear the list
		self.notify_ids[:] = []
