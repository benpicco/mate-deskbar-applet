import cPickle, os
import gtk, gobject
from deskbar import MAX_HISTORY, HISTORY_FILE 
from deskbar.Utils import load_icon
from gettext import gettext as _

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

empty_history_icon = load_icon(gtk.STOCK_STOP)

class EmptyHistoryMatch:
	def get_icon(self):
		return empty_history_icon
	
	def action(self, text=None):
		pass
		
	def get_name(self, text=None):
		return {"msg": _("No History")}
		
	def get_verb(self):
		return "%(msg)s"
		
class DeskbarHistory (gtk.ListStore) :
	"""
	Iterating over a DeskbarHistory with a for loop returns (text,match) pairs.
	Keeps an internal pointer to a history index which you can move with up(), down(),
	and reset(). You retrieve the item in question by get_history().
	
	Text-Match pairs are stored in column 0, while a timestamp (a simple counter really)
	is stored in column 1. The timestamp is used for sorting purposes.
	
	Signals:
		"changed" : emitted when the internal pointer has changed
	"""

	__gsignals__ = {
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
	}
	
	def __init__ (self):
		gtk.ListStore.__init__ (self, gobject.TYPE_PYOBJECT, gobject.TYPE_INT)
		self.set_sort_column_id (1, gtk.SORT_ASCENDING)
		self.set_sort_func (1, self.sort_matches)
		self.timestamp = 0
		self._index = -1
		
	def __iter__ (self):
		return DeskbarHistoryIter (self)				
	
	def set_sort_order (self, order):
		"""order should be one of gtk.SORT_{ASCENDING,DESCENDING}"""
		self.set_sort_column_id (1, order)
	
	def sort_matches (self, model, iter1, iter2):
		if self[iter1][1] > self[iter2][1] :
			return 1
		else:
			return -1
	
	def clear (self):
		gtk.ListStore.clear(self)
		self.timestamp = 0
		self.append(("", EmptyHistoryMatch()))
		self._index = -1
		self.emit("changed")
	
	def clear_stub(self):
		if len(self) == 1 and self[self.get_iter_first()][0][1].__class__ == EmptyHistoryMatch:
			gtk.ListStore.clear(self)
		
	def load (self, module_list):
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
						new_history.append ((text, match))
		except IOError:
			# There's probably no history file
			pass
			
		except Exception, msg:
			return
		
		self.clear()
		if len(new_history) > 0:
			self.clear_stub()
			for hist in new_history:
				self.append (hist)

	def save (self):
		# FIXME: We do not save the timestamp. 
		# This is because we can't break history 
		# file format in the 2.14 series.
		# Is it needed anyway?
		
		# We need ascending sort order for save/load to work correctly
		column_id, old_order = self.get_sort_column_id () # Store the old sort order
		self.set_sort_column_id (1, gtk.SORT_ASCENDING)
		
		save = []
		for text, match in self:
			if match.__class__ == EmptyHistoryMatch:
				return
				
			hsh = match.get_hash(text)
			save.append((text, str(match.get_handler().__class__), str(match.__class__), match.serialize()))
			
		try:
			cPickle.dump(save, file(HISTORY_FILE, 'w'), cPickle.HIGHEST_PROTOCOL)
		except Exception, msg:
			print 'Error:History.save:%s', msg
		pass
		
		# Restore sort order
		self.set_sort_column_id (1, old_order)
	
	def append (self, match_obj):
		gtk.ListStore.append (self, (match_obj, self.timestamp))
		self.timestamp = self.timestamp + 1
	
	def prepend (self, match_obj):
		print "ERROR: DeskbarHistory does not support prepending of matches, use append() instead."
		raise Exception
	
	def add (self, text, match):
		if match.__class__ == EmptyHistoryMatch:
			return
			
		self.clear_stub()
		
		copy_match = True
		for idx, val in enumerate(self):
			htext, hmatch = val
			if (match.get_hash(text), match.__class__) == (hmatch.get_hash(htext), hmatch.__class__):
				match = self[self.get_iter_from_string (str(idx))][0][1]
				self.remove (self.get_iter_from_string (str(idx)))
				copy_match = False
				break

		if copy_match:
			copy = match.copy()
			if copy != None:
				match = copy
				
		self.append ((text, match))
		if len(self) > MAX_HISTORY:
			# Remove the last element
			last = self.get_iter_from_string (str(len(self) - 1))
			self.remove (last)

		self.reset()
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
