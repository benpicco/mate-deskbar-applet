import os
import re
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from deskbar.defs import VERSION
from deskbar.core.Utils import load_icon
import deskbar.interfaces.Action
import deskbar.interfaces.Match
import deskbar.interfaces.Module
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
import gtk
from gettext import gettext as _

HANDLERS = ["TomboyNotesModule"]

# Handle opening a note
class TomboyOpenNoteAction (deskbar.interfaces.Action):

	def __init__(self, note, title):
		deskbar.interfaces.Action.__init__(self, title)
		self._note = note
		self._title = title

	def activate(self, text=None):
		tomboy().DisplayNote(self._note)

	def get_icon(self):
		return "tomboy-note"
		
	def get_hash(self):
		return "DESKBAROPEN: %s" % self._title
		
	def get_verb(self):
		return _("Open note <b>%(name)s</b>")

	def is_valid(self, text=None):
		return (not tomboy() == None) and tomboy().NoteExists(self._note)
		
# Handle deleting a note
class TomboyDeleteNoteAction (TomboyOpenNoteAction):

	def activate(self, text=None):
		if self.really_delete(): tomboy().DeleteNote(self._note)

	def really_delete(self):
		dialog = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION)
		title = _("Really delete this note?")
		content = _("If you delete a note it is permanently lost.")
		dialog.set_markup("<span size='larger' weight='bold'>%s</span>\n\n%s" % (title, content) )
		dialog.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL )
		dialog.add_button( gtk.STOCK_DELETE, gtk.RESPONSE_ACCEPT )
		resp = dialog.run()
		dialog.destroy()
		return resp == gtk.RESPONSE_ACCEPT

	def get_icon(self):
		return "edit-delete"

	def get_verb(self):
		return _("Delete note <b>%(name)s</b>")

	def get_hash(self):
		return "DESKBARDELETE: %s" % self._title
	
	def skip_history(self):
		return True

# Handle creating and opening a note
class TomboyCreateNoteAction (deskbar.interfaces.Action):
	
	def __init__(self, title):
		deskbar.interfaces.Action.__init__(self, title)
		self._title = title
		self._note = None
	
	def activate(self, text=None):
		if self.is_valid(): 
			self._note = tomboy().CreateNamedNote( self._title )
		tomboy().DisplayNote(self._note)
		
	def get_icon(self):
		return "tomboy"
		
	def get_verb(self):
		return _("Create note <b>%(name)s</b>")
	
	def get_hash(self):
		return "DESKBARCREATE: %s" % self._title
	
	def skip_history(self):
		return True
	
	def is_valid(self, text=None):
		return tomboy().FindNote(self._title) == ''

# Match for existing notes
class TomboyExistingNoteMatch (deskbar.interfaces.Match):

	def __init__(self, note, **kwargs):
		self.title = tomboy().GetNoteTitle(note)
		deskbar.interfaces.Match.__init__(self,
			name= self.title,
			icon="tomboy-note", category="notes", **kwargs)
		self.note = note
		self.add_action( TomboyOpenNoteAction(self.note, self.title) )
		self.add_action( TomboyDeleteNoteAction(self.note, self.title) )
		self.add_action( CopyToClipboardAction(_("Title"), self.title) )
		self.add_action( CopyToClipboardAction(_("Contents"), tomboy().GetNoteContents(self.note) ))
		
	def get_hash(self, text=None):
		return self.note

# Match for notes we shall have to create
class TomboyCreateNoteMatch (deskbar.interfaces.Match):
	
	def __init__(self, title, **kwargs):
		self.title = title
		deskbar.interfaces.Match.__init__(self,
			name= self.title,
			icon="tomboy", category="actions", **kwargs)
		self.add_action( TomboyCreateNoteAction(self.title) )

# Overall module
class TomboyNotesModule (deskbar.interfaces.Module):

	INFOS = {'icon': load_icon("tomboy"),
		'name': _('Tomboy Notes'),
		'description': _('Search your Tomboy notes'),
		'version': VERSION,
		}
	
	tomboy = None
	
	def __init__(self):
		deskbar.interfaces.Module.__init__(self)
	
	def initialize(self):
		TomboyNotesModule.tomboy = get_tomboy_connection()
	
	# This is so when Tomboy is disabled, history items won't try to connect
	# Otherwise, we get big DBus errors
	def set_enabled(self, val):
		if val == False: TomboyNotesModule.tomboy = None
		deskbar.interfaces.Module.set_enabled(self, val)
	
	# Handles the return from the Tomboy method SearchNotes
	# This should be called from the lambda in query so that it will get
	# the extra information (the query text)
	def handle_searchnotes( self, text, notes ):
		for note in notes:
			if tomboy().NoteExists(note):
				self._emit_query_ready( text, [TomboyExistingNoteMatch(note)] )
	
	def handle_dbus_error(self, e): print e
	
	def query(self, text):
		if len(text) >= 3:
			case = text[0].capitalize() + text[1:]
			if tomboy().FindNote(case) == '':
				self._emit_query_ready( text, [TomboyCreateNoteMatch(case)] )
			# Search for the note (not case-sensitive)
			# The query text needs to be lowercase, for reasons I do not fathom
			tomboy().SearchNotes( text.lower(), dbus.Boolean(False), 
				# A lambda, because otherwise the handler won't get the query text
				reply_handler=lambda notes: self.handle_searchnotes( text, notes ),
				error_handler=self.handle_dbus_error )
	
	@staticmethod
	def has_requirements():
		return tomboy_installed() and tomboy_correct_version()

# Returns connection to Tomboy
def get_tomboy_connection():
	dbus_loop = DBusGMainLoop()
	bus = dbus.SessionBus( mainloop=dbus_loop )
	tomboy_obj = bus.get_object( "org.gnome.Tomboy", "/org/gnome/Tomboy/RemoteControl" )
	return dbus.Interface( tomboy_obj, "org.gnome.Tomboy.RemoteControl" )

# Make it easier to use the Tomboy connection
# Otherwise, we would have to do TomboyNotesModule.tomboy() all the time
def tomboy():
	return TomboyNotesModule.tomboy

# Check if Tomboy is on DBus
def tomboy_installed():
	bus = dbus.SessionBus()
	proxy = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
	_dbus = dbus.Interface(proxy, 'org.freedesktop.DBus')
	_dbus.ReloadConfig()
	bus_names = _dbus.ListActivatableNames()
	if "org.gnome.Tomboy" in bus_names:
		return True
	else:
		TomboyNotesModule.INSTRUCTIONS = _("Tomboy does not seem to be installed.")
		return False

# Parse Tomboy command line output to get version
# If we use DBus, it will wake up Tomboy even if 
# this module isn't enabled.
def get_tomboy_version():
	command = os.popen("tomboy --version")
	read = command.read()
	command.close()
	
	line_regexp = re.compile( 'Version \d\.\d\.\d', re.IGNORECASE )
	version_line = line_regexp.findall( read )[0].strip()
	number_regexp = re.compile( '\d\.\d\.\d' )
	version = number_regexp.findall( version_line )[0]
	return version

# Check if version is correct
def tomboy_correct_version():
	wanted = "0.9.2"
	actual =  get_tomboy_version()
	_wanted = wanted.split(".")
	_actual = actual.split(".")
	if _actual[0] > _wanted[0]:
		return True
	elif _actual[0] == _wanted[0]:
		if _actual[1] > _wanted[1]:
			return True
		elif _actual[1] == _wanted[1] and _actual[2] >= _wanted[2]:
			return True
	TomboyNotesModule.INSTRUCTIONS = _("Tomboy does not seem to be the correct version.\nTomboy %s or greater must be installed.") % wanted
	return False
	
