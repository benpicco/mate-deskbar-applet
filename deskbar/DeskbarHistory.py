import cPickle, os
import gtk, gobject
from deskbar import MAX_HISTORY, HISTORY_FILE, MAX_RESULTS_PER_HANDLER

class DeskbarHistoryIter : 
	"""An iter type to iterate over a DeskbarHistory.
	This object is (typically) not used directly.
	For documentation on iters see: http://docs.python.org/lib/typeiter.html
	"""
	def __init__ (self, owner):
		self.owner = owner
		self.owner_iter = owner.get_iter_first ()
		
	def __iter__ (self):
		return self
		
	def next (self):
		try:
			item = self.owner[self.owner_iter][0]
			self.owner_iter = self.owner.iter_next (self.owner_iter)
		except TypeError:
			raise StopIteration
		return item

# The sort function ids
SORT_CHRONOLOGICAL = 1

class SortedDeskbarHistory (gtk.TreeModelSort):	
	def __init__(self):
		gtk.TreeModelSort.__init__(self, get_deskbar_history())
		self.set_sort_func(SORT_CHRONOLOGICAL, self.on_sort_chronological)
		self.set_sort_column_id(SORT_CHRONOLOGICAL, gtk.SORT_ASCENDING)
	
	def set_sort_order(self, order):
		#self.set_sort_column_id(SORT_CHRONOLOGICAL, order)
		# Somehow this triggers a segfault !
		pass
	
	def on_sort_chronological(self, model, iter1, iter2):
		return 1

class DeskbarHistory (gtk.ListStore) :
	"""
	Iteraating over a DeskbarHistory with a for loop returns (text,match) pairs.
	Keeps an internal pointer to a history index which you can move with up(), down(),
	and reset(). You retrieve the item in question by get_history().
	
	Signals:
		"changed" : emitted when the internal pointer has changed
	"""

	__gsignals__ = {
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
	}
	
	def __init__ (self):
		gtk.ListStore.__init__ (self, gobject.TYPE_PYOBJECT)
		self._index = -1
		
	def __iter__ (self):
		return DeskbarHistoryIter (self)				
	
	def clear (self):
		gtk.ListStore.clear(self)
		self._index = -1
		self.emit("changed")
		
	def load (self, module_list):
		print 'Loading History'
		new_history = []
		try:
			saved_history = cPickle.load(file(HISTORY_FILE))
			
			def strip_class(name):
				i = name.rfind(".")
				if i == -1:
					return None
					
				return name[i+1:]
						
			for text, handler_class_name, match_class_name, serialized in saved_history:
				for modctx in module_list:
					if strip_class(handler_class_name) != modctx.handler:
						continue
					
					match_class = strip_class(match_class_name)
					if match_class == None:
						continue
						
					match = modctx.module.deserialize(match_class, serialized)
					if match != None:
						new_history.append ([(text, match)])
		except Exception, msg:
			return
		
		if len(new_history) > 0:
			self.clear()
			for hist in new_history:
				self.append (hist)
		
	def save (self):
		save = []
		for text, match in self:
			hsh = match.get_hash(text)
			save.append((text, str(match.get_handler().__class__), str(match.__class__), match.serialize()))
			
		try:
			cPickle.dump(save, file(HISTORY_FILE, 'w'), cPickle.HIGHEST_PROTOCOL)
		except Exception, msg:
			print 'Error:History.save:%s', msg
		pass
	
	def add (self, text, match):
		copy_match = True
		for idx, val in enumerate(self):
			htext, hmatch = val
			if (text, match.__class__) == (htext, hmatch.__class__):
				match = self[self.get_iter_from_string (str(idx))][0][1]
				self.remove (self.get_iter_from_string (str(idx)))
				copy_match = False
				break

		if copy_match:
			copy = match.copy()
			if copy != None:
				match = copy
				
		self.prepend ([(text, match)])
		if len(self) > MAX_HISTORY:
			# Remove the last element
			last = self.get_iter_from_string (str(len(self) - 1))
			self.remove (last)
		self._index = -1
		self.save()
	
	def up(self):
		if self._index < len(self)-1:
			self._index = self._index + 1
			self.emit('changed')
	
	def down(self):
		if self._index > -1:
			self._index = self._index - 1
			self.emit('changed')
	
	def reset(self):
		if self._index != -1:
			self._index = -1
			self.emit('changed')
	
	def last(self):
		if len(self) == 0:
			return None
		last = self.get_iter_from_string (str(len(self) - 1))
		return self[last][0]
	
	def get_all_history(self):
		return self
		
	def get_history(self):
		if self._index == -1:
			return None
		return self[self.get_iter_from_string (str(self._index))][0]
	
if gtk.pygtk_version < (2,8,0):
	gobject.type_register(DeskbarHistory)
	
shared_history = DeskbarHistory()
def get_deskbar_history():
	return shared_history
