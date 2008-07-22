from dbus.mainloop.glib import DBusGMainLoop
from deskbar.core.Utils import load_icon
from deskbar.defs import VERSION
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from gettext import gettext as _
import dbus
import deskbar.interfaces.Action
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gtk
import logging
import subprocess
import re

LOGGER = logging.getLogger(__name__)

HANDLERS = ["TomboyNotesModule"]

# Handle opening a note
class TomboyOpenNoteAction (deskbar.interfaces.Action):

    def __init__(self, note, title):
        deskbar.interfaces.Action.__init__(self, title)
        self._note = note
        self._title = title

    def activate(self, text=None):
        try:
            tomboy().DisplayNote(self._note)
        except (dbus.DBusException, dbus.exceptions.DBusException), e:
            LOGGER.exception(e)
            return

    def get_icon(self):
        return "note.png"
        
    def get_hash(self):
        return "DESKBAROPEN: %s" % self._title
        
    def get_verb(self):
        return _("Open note <b>%(name)s</b>")

    def is_valid(self, text=None):
        try:
            return (not tomboy() == None) and tomboy().NoteExists(self._note)
        except (dbus.DBusException, dbus.exceptions.DBusException), e:
            LOGGER.exception(e)
            return False
        
# Handle deleting a note
class TomboyDeleteNoteAction (TomboyOpenNoteAction):

    def activate(self, text=None):
        try:
            if self.really_delete(): tomboy().DeleteNote(self._note)
        except (dbus.DBusException, dbus.exceptions.DBusException), e:
            LOGGER.exception(e)
            return

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
        try:
            if self.is_valid(): 
                self._note = tomboy().CreateNamedNote( self._title )
            tomboy().DisplayNote(self._note)
        except (dbus.DBusException, dbus.exceptions.DBusException), e:
            LOGGER.exception(e)
            return    
        
    def get_icon(self):
        return "note-new.png"
        
    def get_verb(self):
        return _("Create note <b>%(name)s</b>")
    
    def get_hash(self):
        return "DESKBARCREATE: %s" % self._title
    
    def skip_history(self):
        return True
    
    def is_valid(self, text=None):
        try:
            return tomboy().FindNote(self._title) == ''
        except (dbus.DBusException, dbus.exceptions.DBusException), e:
            LOGGER.exception(e)
            return False

# Match for existing notes
class TomboyExistingNoteMatch (deskbar.interfaces.Match):

    def __init__(self, note, **kwargs):
        self.title = tomboy().GetNoteTitle(note)
        deskbar.interfaces.Match.__init__(self,
            name= self.title,
            icon="note.png", category="notes", **kwargs)
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
            icon="note-new.png", category="actions", **kwargs)
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
         
    def stop(self):
        TomboyNotesModule.tomboy = None
    
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
            try:
                if tomboy().NoteExists(note):
                    match = TomboyExistingNoteMatch(note)
                    match.set_priority (self.get_priority())
                    self._emit_query_ready( text, [match] )
            except (dbus.DBusException, dbus.exceptions.DBusException), e:
                LOGGER.exception(e)
                return
    
    def handle_dbus_error(self, e): LOGGER.error(e)
    
    def query(self, text):
        if len(text) >= 3:
            case = text[0].capitalize() + text[1:]
            try:
                if tomboy().FindNote(case) == '':
                    match = TomboyCreateNoteMatch(case)
                    match.set_priority (self.get_priority())
                    self._emit_query_ready( text, [match] )
            except (dbus.DBusException, dbus.exceptions.DBusException), e:
                LOGGER.exception(e)
                return
               
            # Search for the note (not case-sensitive)
            # The query text needs to be lowercase, for reasons I do not fathom
            try:
                tomboy().SearchNotes( text.lower(), dbus.Boolean(False), 
                    # A lambda, because otherwise the handler won't get the query text
                    reply_handler=lambda notes: self.handle_searchnotes( text, notes ),
                    error_handler=self.handle_dbus_error )
            except (dbus.DBusException, dbus.exceptions.DBusException), e:
                LOGGER.exception(e)
                return
    
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
    try:
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
    except (dbus.DBusException, dbus.exceptions.DBusException), e:
        LOGGER.exception(e)
        return False

# Parse Tomboy command line output to get version
# If we use DBus, it will wake up Tomboy even if 
# this module isn't enabled.
def get_tomboy_version():
    try:
        process = subprocess.Popen("tomboy --version", shell=True,
                                   stdout=subprocess.PIPE)
        process.wait()
        command = process.stdout
        read = command.read()
        command.close()
    except OSError, e:
        LOGGER.exception(e)
        return '0.0.0'
    
    line_regexp = re.compile( 'Version (\d+?)\.(\d+?)\.(\d+?)', re.IGNORECASE )
    results_list = line_regexp.findall( read )
    if len(results_list) == 0:
        return '0.0.0'
    else:
        return [int(i) for i in results_list[0]]

# Check if version is correct
def tomboy_correct_version():
    wanted = "0.9.2"
    _actual =  get_tomboy_version()
    _wanted = [int(i) for i in wanted.split(".")]
    if _actual[0] > _wanted[0]:
        return True
    elif _actual[0] == _wanted[0]:
        if _actual[1] > _wanted[1]:
            return True
        elif _actual[1] == _wanted[1] and _actual[2] >= _wanted[2]:
            return True
    TomboyNotesModule.INSTRUCTIONS = _("Tomboy does not seem to be the correct version.\nTomboy %s or greater must be installed.") % wanted
    return False
    
