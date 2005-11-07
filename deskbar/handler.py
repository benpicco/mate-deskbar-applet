from os.path import join
import gtk, gobject
import deskbar, deskbar.handler_utils

class Match:
	def __init__(self, handler, name, icon=None):
		self._priority = 0
		self._handler = handler
		self._name = name
		self._icon = icon
	
	def get_handler(self):
		"""
		Returns the handler owning this match.
		"""
		return self._handler
		
	def get_name(self, text=None):
		"""
		Returns a dictionary whose entries will be used in the Action
		string returned by get_verb.
		
		The passed string is the complete query string.
		
		The resulting action text will be
		match.get_verb() % match.get_name(query)
		
		Remember to escape pango markup if needed.
		"""
		return {"name": self._name}
		
	def get_verb(self):
		"""
		Returns the action string associated to this handler.
		
		The string must contain one or more "%(name)s" that will
		be replaced by the match get_name().
		
		The %(text)s will be replaced by the typed text.
		By default the %(name)s will be replaced by the self._name
		
		The string can also contain pango markup.
		
		Examples:
		 Send mail to %(address)s
		 Search <b>%s</b> for %(text)s
		 Execute %(prog)s
		"""
		raise NotImplementedError
		
	def get_priority(self):
		"""
		Returns the priority of the given match as int.
		This number can be used to compare the match from the
		same handler.
		"""
		return self._priority
	
	def get_hash(self, text=None):
		"""
		Returns a hash used to verify if a query has one or more duplicates.
		Matches that have same hash will be selected based on the handler priority.
		text is the entered query string.
		"""
		raise NotImplementedError
		
	def get_icon(self):
		"""
		Returns a GdkPixbuf hat represents this match.
		Returns None if there is no associated icon.
		"""
		return self._icon
		
	def action(self, text=None):
		"""
		Tell the match to do the associated action.
		This method should not block.
		The optional text is the additional argument entered in the entry
		"""
		raise NotImplementedError
		
class Handler:
	def __init__(self, iconfile):
		"""
		The constructor of the Handler should not block. 
		Heavy duty tasks such as indexing should be done in the initialize() method.
		Under all circumstances, the constructor should not raise ANY exception
		"""
		self._icon = deskbar.handler_utils.load_icon(iconfile)
	
	def set_priority(self, prio):
		self._priority = prio
		
	def get_priority(self):
		"""
		Returns the global priority (against other handlers) of this handler as int
		"""
		return self._priority
		
	def get_icon(self):
		"""
		Returns a GdkPixbuf hat represents this handler.
		Returns None if there is no associated icon.
		"""
		return self._icon
	
	def initialize(self):
		"""
		The initialize of the Handler should not block. 
		Heavy duty tasks such as indexing should be done in this method, it 
		will be called with a low priority in the mainloop.
		
		Handler.initialize() is guarantied to be called before the handler
		is queried.
		
		If an exception is thrown in this method, the module will be ignored and will
		not receive any query.
		"""
		pass
	
	def stop(self):
		"""
		If the handler needs any cleaning up before it is unloaded, do it here.
		
		Handler.stop() is guarantied to be called before the handler is 
		unloaded.
		"""
		pass
		
	def query(self, query, max=5):
		"""
		Searches the handler for the given query string.
		Returns a list of matches objects of maximum length
		"max".
		"""
		raise NotImplementedError

	def is_async (self):
		"""
		AsyncHandler overwrites this method and returns True.
		It is used to determine whether we should call some async specific methods/signals.
		"""
		return False

class SignallingHandler (Handler, gobject.GObject):
	"""
	This handler is an asynchronous handler using natural glib libraries, like
	libebook, or galago, or twisted.
	"""
	__gsignals__ = {
		"query-ready" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
	}

	def __init__ (self, iconfile=None):
		Handler.__init__ (self, iconfile)
		gobject.GObject.__init__ (self)
		self.__last_query = ""

	def query_async (self, qstring, max=5):
		"""
		When we receive an async call, we first register the most current search string.
		Then we call with a little delay the actual query() method, implemented by the handler.
		
		This is to avoid searching too many times, the delay can be slow like 150ms.
		"""
		self.__last_query = qstring
		gobject.timeout_add(150, self.__query_if_valid, qstring, max)
	
	def __query_if_valid(self, qstring, max):
		"""
		This is called from a glib's timeout, we check if the string still is valid, then
		proceed to calling query(). We return None, meaning that the timer expires.
		"""
		if self.__last_query == qstring:
			self.query (qstring, max)

	def emit_query_ready (self, matches, qstring):
		if qstring == self.__last_query:
			self.emit ("query-ready", matches)

	def stop_query (self):
		self.__last_query = None
		
	def is_async (self):
		return True
		
if gtk.gtk_version < (2,8,0):
	gobject.type_register(SignallingHandler)
	
# Here begins the Nastyness
from Queue import Queue
from Queue import Empty
from threading import Thread

class NoArgs :
	pass

class QueryStopped (Exception):
	pass	

class QueryChanged (Exception):
	def __init__ (self, new_query):
		self.new_query = new_query
				
class AsyncHandler (Handler, gobject.GObject):
	"""
	This class can do asynchronous queries. To implement an AsyncHandler just write it
	like you would an ordinary (sync) Handler. Ie. you main concern is to implement a
	query() method.
	
	In doing this you should regularly call check_query_changed() which will restart
	the query if the query string has changed. This method can handle clean up methods
	and timeouts/delays if you want to check for rapidly changing queries.
	
	To return a list of Matches either just return it normally from query(), or use
	emit_query_ready(matches) to emit partial results.
	
	There will at all times only be at maximum one thread per AsyncHandler.
	"""

	__gsignals__ = {
		"query-ready" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}

	QUERY_PRIORITY = gobject.PRIORITY_DEFAULT_IDLE

	def __init__ (self, iconfile=None):
		Handler.__init__ (self, iconfile)
		gobject.GObject.__init__ (self)
		self.__query_queue = Queue ()
		self.is_running = False
	
	def query_async (self, qstring, max=5):
		"""
		This method is the one to be called by the object wanting to start a new query.
		If there's an already running query that one will be cancelled if possible.
		
		Each time there is matches ready there will be a "query-ready" signal emitted
		which will be handled in the main thread. A list of Match objects will be passed
		argument to this signal.
		
		Note: An AsyncHandler may signal on partial results. The thread need not have
		exited because there's a 'query-ready' signal emitted. Read: Don't assume that the
		handler only return Matches one time.
		"""
		if not self.is_running:
			self.is_running = True
			Thread (None, self.__query_async, args=(qstring, max)).start ()
			print "AsyncHandler: Thread created for %s" % self.__class__
		else:
			self.__query_queue.put (qstring, False)
	
	def stop_query (self):
		"""
		Instructs the handler to stop the query the next time it does check_query_changed().
		"""
		self.__query_queue.put (QueryStopped)
	
	def emit_query_ready (self, matches):
		"""
		Use this method to emit partial results. matches should be a list of Match objects.
		
		Note: returning a list of Match objects from the query() method automatically
		emits a 'query-ready' signal for this list. 
		"""
		gobject.idle_add (self.__emit_query_ready, matches)
		
	def check_query_changed (self, clean_up=None, args=NoArgs, timeout=None):
		"""
		Checks if the query has changed. If it has it will execute clean_up(args)
		and raise a QueryChanged exception. DO NOT catch this exception. This should
		only be done by __async_query().
		
		If you pass a timeout argument this call will not return before the query
		has been unchanged for timeout seconds.
		"""
		qstring = None
		try:
			qstring = self.__get_last_query (timeout)
		except QueryStopped:
			if clean_up:
				if args == NoArgs:
					clean_up ()
				else:
					clean_up (args)
			raise QueryStopped()
		if qstring:
			# There's a query queued
			# cancel the current query.
			if clean_up:
				if args == NoArgs:
					clean_up ()
				else:
					clean_up (args)
			raise QueryChanged (qstring)
		
	def __emit_query_ready (self, matches):
		"""Idle handler to emit a 'query-ready' signal to the main loop."""
		self.emit ("query-ready", matches)
		return False

	def __query_async (self, qstring, max=5):
		"""
		The magic happens here.
		"""
		try:
			res = self.query (qstring, max)
			if (res and res != []):
				self.emit_query_ready (res)
			self.is_running = False
			
		except QueryChanged, query_change:
			try:
				self.__query_async (query_change.new_query, max)
			except QueryStopped:
				self.is_running = False
				print "AsyncHandler: %s thread terminated." % str(self.__class__)
				
		except QueryStopped:
			self.is_running = False
			print "AsyncHandler: %s thread terminated." % str(self.__class__)

	def __get_last_query (self, timeout=None):
		"""
		Returns the query to be put on the query queue. We don't wan't to
		do all the intermediate ones... They're obsolete.
		
		If there's a QueryStopped class somewhere in the queue 
		(put there by stop_query()) raise a QueryStopped exeption.
		This exception will be caught by __query_async()
		
		If timeout is passed then wait timeout seconds to see if new queries
		are put on the queue.
		"""
		tmp = None
		last_query = None
		try:
			while True:
				# Get a query without blocking (or only block
				# timeout seconds).
				# The get() call raises an Empty exception
				# if there's no element to get()
				if timeout:
					tmp = self.__query_queue.get (True, timeout)
				else:
					tmp = self.__query_queue.get (False)
				last_query = tmp
				if last_query == QueryStopped:
					raise QueryStopped ()
		except Empty:
			return last_query

	def is_async (self):
		"""Well what do you think?"""
		return True

if gtk.gtk_version < (2,8,0):
	gobject.type_register(AsyncHandler)
