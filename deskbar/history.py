import cPickle, os
from deskbar import MAX_HISTORY
import deskbar.handler

class DeskbarHistory:
	def __init__(self, applet):
		self.applet = applet
		self._history = []
		
#		print 'Loading hitsory'
#		try:
#			save = cPickle.load(file(applet.prefs.HISTORY))
#			print save
#			for text, fun, data in save:
#				match = fun(*data)
#				self._history.append((text, match))
#		except Exception, msg:
#			print 'Error:History:', msg
			
			
		self._index = -1
		
	def add(self, text, match):
		for htext, hmatch in self._history:
			if (text, match.__class__) == (htext, hmatch.__class__):
				self._history.remove((htext, hmatch))

		self._history.insert(0, (text, match))
		self._history = self._history[:MAX_HISTORY]
		self._index = -1
	
	def up(self):
		if self._index < len(self._history)-1:
			self._index = self._index + 1
	
	def down(self):
		if self._index > -1:
			self._index = self._index - 1
	
	def reset(self):
		self._index = -1
	
	def last(self):
		if len(self._history) == 0:
			return None
		return self._history[0]
	
	def get_all_history(self):
		return self._history
		
	def get_history(self):
		if self._index == -1:
			return None
		
		return self._history[self._index]
	
	def save(self):
#		save = []
#		for text, match in self._history:
#			fun, data = match.serialize()
#			save.append((text, fun, data))
#			
#		try:
#			cPickle.dump(save, file(self.applet.prefs.HISTORY, 'w'), cPickle.HIGHEST_PROTOCOL)
#			print 'History saved:',  save
#		except Exception, msg:
#			print 'Error:History.save:%s', msg
		pass
