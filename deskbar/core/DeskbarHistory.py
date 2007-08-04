import cPickle, os
import gtk, gobject
import time
import logging
import deskbar.interfaces.Action
from deskbar import MAX_HISTORY, HISTORY_FILE 
from deskbar.core.Utils import load_icon
from gettext import gettext as _

class EmptyHistoryAction(deskbar.interfaces.Action):
	
	def __init__(self):
		deskbar.interfaces.Action.__init__(self, _("No History"))
	
	def activate(self, text=None):
		pass
		
	def get_verb(self):
		return "%(name)s"
		
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

	__instance = None
	(COL_TIME, COL_TEXT, COL_ACTION) = range(3)
	
	def __init__ (self):
		gtk.ListStore.__init__ (self, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT) # timestamp, query, match
		self.set_sort_column_id (self.COL_TIME, gtk.SORT_ASCENDING)
		self.set_sort_func (self.COL_TIME, self.sort_actions)
		self.set_sort_order(gtk.SORT_DESCENDING)
		self._index = -1
	
	@staticmethod
	def get_instance():
		if not DeskbarHistory.__instance:
			DeskbarHistory.__instance = DeskbarHistory()
		return DeskbarHistory.__instance
    
	def set_sort_order (self, order):
		"""order should be one of gtk.SORT_{ASCENDING,DESCENDING}"""
		self.set_sort_column_id (self.COL_TIME, order)
	
	def sort_actions (self, model, iter1, iter2):
		if self[iter1][self.COL_TIME] > self[iter2][self.COL_TIME] :
			return 1
		else:
			return -1
	
	def clear (self):
		gtk.ListStore.clear(self)
		#self.append("", "", EmptyHistoryAction())
		self._index = -1
	
	def clear_stub(self):
		if len(self) == 1 and self[self.get_iter_first()][self.COL_ACTION].__class__ == EmptyHistoryAction:
			gtk.ListStore.clear(self)
		
	def load (self, module_list):
		new_history = []
		try:
			saved_history = cPickle.load(file(HISTORY_FILE))
			
			for timestamp, text, action in saved_history:
				self.append(timestamp, text, action)
			
		except IOError:
			# There's probably no history file
			pass

	def save (self):
		save = []
		for timestamp, text, action in self:
			if action.__class__ != EmptyHistoryAction:
				save.append((timestamp, text, action))
		
		try:
			cPickle.dump(save, file(HISTORY_FILE, 'w'), cPickle.HIGHEST_PROTOCOL)
		except Exception, msg:
			logging.error('History.save:%s', msg)
		pass
	
	def append (self, timestamp, text, action):
		gtk.ListStore.append (self, (timestamp, text, action))
	
	def prepend (self, timestamp, text, action):
		raise NotImplementError("DeskbarHistory does not support prepending of matches, use append() instead.")
	
	def add (self, text, action):
		if action.__class__ == EmptyHistoryAction:
			return
		if action.skip_history():
			self.reset()
			return
			
		self.clear_stub()
		
		for idx, val in enumerate(self):
			htime, htext, haction = val
			if (action.get_hash() == haction.get_hash() and action.__class__.__name__ == haction.__class__.__name__):
				self.remove (self.get_iter_from_string (str(idx)))
				break
				
		timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
		self.append (timestamp, text, action)
		if len(self) > MAX_HISTORY:
			# Remove the last element
			last = self.get_iter_from_string (str(len(self) - 1))
			self.remove (last)

		self.reset()
		self.save()
	
	def up(self):
		if self._index < len(self)-1:
			self._index = self._index + 1
			return self.get_current()
	
	def down(self):
		if self._index > -1:
			self._index = self._index - 1
			return self.get_current()
	
	def reset(self):
		if self._index != -1:
			self._index = -1
			return self.get_current()
	
	def last(self):
		if len(self) == 0:
			return None
		last = self.get_iter_from_string (str(len(self) - 1))
		return self[last][self.COL_ACTION]
	
	def get_all(self):
		return self
		
	def get_current(self):
		if self._index == -1:
			return None
		col_id, direction = self.get_sort_column_id()
		index = self._index
		if direction == gtk.SORT_ASCENDING:
			index = len(self)-1-index

		row = self[self.get_iter_from_string (str(index))]
		return (row[self.COL_TEXT], row[self.COL_ACTION])
	
if gtk.pygtk_version < (2,8,0):
	gobject.type_register(DeskbarHistory)
