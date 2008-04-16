from deskbar.core.Utils import is_program_in_path, load_icon
from deskbar.core.Categories import CATEGORIES
from deskbar.defs import VERSION
from deskbar.handlers.actions.ActionsFactory import get_actions_for_uri
from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from deskbar.handlers.actions.OpenFileAction import OpenFileAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from os.path import basename
from gobject import GError
import cgi, re
import deskbar, deskbar.interfaces.Module
import deskbar.interfaces.Match
import gnomevfs
import logging
import threading

LOGGER = logging.getLogger(__name__)

MAX_RESULTS = 20 # per handler
HANDLERS = ["BeagleLiveHandler"]

try:
    import beagle
except:
    # If this fails we complain about it in _check_requirements()
    # so do nothing now
    pass

class BeagleType:
    """
    You should at least set name_properties
    and category
    """
    
    def __init__(self):
        self.__name_properties = []
        self.__extra_properties = {}
        self.__category = "default"
        self.__snippet = False
    
    def set_name_properties(self, val):
        """
        Properties that should contain the name
        of the item
        
        When the beagle match doesn't contain the
        first property the second one is retrieved
        and so on
        
        @type val: tuple or list
        """
        self.__name_properties = val
        
    def get_name_properties(self):
        return self.__name_properties
 
    def set_extra_properties(self, val):
        self.__extra_properties = val
        
    def get_extra_properties(self):
        """
        @return: A dict containing key:template pairs to search for
        """
        return self.__extra_properties
    
    def set_category(self, val):
        """
        Set the deskbar category
        """
        self.__category = val
        
    def get_category(self):
        return self.__category
    
    def set_has_snippet(self, val):
        self.__snippet = val
    
    def get_has_snippet(self):
        return self.__snippet
    
class ContactType(BeagleType):
    
    def __init__(self):
        BeagleType.__init__(self)
        self.set_name_properties(("fixme:FileAs",))
        self.set_category("people")
        
class MailMessageType(BeagleType):
    
    def __init__(self):
        BeagleType.__init__(self)
        self.set_name_properties(("dc:title",
                                  "parent:dc:title",))
        self.set_extra_properties({"sender": ("fixme:from_name",
                                              "parent:fixme:from_name",)
        })
        self.set_category("emails")
        
class FileType(BeagleType):
    
    def __init__(self):
        BeagleType.__init__(self)
        self.set_name_properties(("beagle:ExactFilename",))
        self.set_extra_properties({"inside_archive": ("fixme:inside_archive",),
                                   "parent_file": ("parent:beagle:ExactFilename",)
                                  })
        self.set_category("files")
        self.set_has_snippet(True)
 
class DirectoryType(FileType):
    
    def __init__(self):
        FileType.__init__(self)
        self.set_category("places")
        self.set_has_snippet(False)

class DocumentType(FileType):
    
    def __init__(self):
        FileType.__init__(self)
        self.set_category("documents")
        
class AudioType(FileType):
    
    def __init__(self):
        FileType.__init__(self)
        self.set_category("audio")
        self.set_has_snippet(False)
        
class VideoType(FileType):
    
    def __init__(self):
        FileType.__init__(self)
        self.set_category("video")
        self.set_has_snippet(False)
        
class ImageType(FileType):
    
    def __init__(self):
        FileType.__init__(self)
        self.set_category("images")
        self.set_has_snippet(False)
    
class FeedItemType(BeagleType):
    
    def __init__(self):
        BeagleType.__init__(self)
        self.set_name_properties(("dc:title",))
        self.set_extra_properties({"publisher": ("dc:publisher",),
                                   "identifier": ("dc:identifier",)
                                   })
        self.set_category("news")
        self.set_has_snippet(True)
        
class NoteType(BeagleType):
    
    def __init__(self):
        BeagleType.__init__(self)
        self.set_name_properties(("dc:title",))
        self.set_category("notes")
        self.set_has_snippet(True)
        
class IMLogType(BeagleType):
    
    def __init__(self):
        BeagleType.__init__(self)
        self.set_name_properties(("fixme:speakingto",))
        self.set_extra_properties({"client": ("fixme:client",)})
        self.set_category("conversations")
        self.set_has_snippet(True)
    
class CalendarType(BeagleType):
    
    def __init__(self):
        BeagleType.__init__(self)
        self.set_name_properties(("fixme:summary",))
        self.set_category("documents")
        
class WebHistoryType(BeagleType):
    
    def __init__(self):
        BeagleType.__init__(self)
        # FIX-BEAGLE bug #330053, dc:title returns as None even though it _is_ set
        self.set_name_properties(("dc:title",))
        self.set_category("web")
        
TYPES = {
    "Contact": ContactType(),
    "MailMessage": MailMessageType(),
    "File": FileType(),
    "Directory": DirectoryType(),
    "Document": DocumentType(),
    "Audio": AudioType(),
    "Video": VideoType(),
    "Image": ImageType(), 
    "FeedItem": FeedItemType(),
    "Note": NoteType(),
    "IMLog": IMLogType(),
    "Calendar": CalendarType(),
    "WebHistory": WebHistoryType(),
}

# See section FileType at http://beagle-project.org/Writing_clients
BEAGLE_FILE_TYPE_TO_TYPES_MAP = {
    "document": "Document",
    "archive": "File",
    "audio": "Audio",
    "video": "Video",
    "image": "Image",
    "source": "File",
    "documentation": "Document",
    "directory": "Directory",
}

### ===== END: TYPES ===== ###

class OpenWithEvolutionAction(OpenWithApplicationAction):
    def __init__(self, name, uri):
        OpenWithApplicationAction.__init__(self, name, "evolution", [uri])
        
class OpenContactAction(OpenWithEvolutionAction):
    def __init__(self, name, uri):
        OpenWithEvolutionAction.__init__(self, name, uri)
        
    def get_icon(self):
        return "stock_contact"
    
    def get_verb(self):
        return _("Edit contact %s") % "<b>%(name)s</b>"
    
class OpenMailMessageAction(OpenWithEvolutionAction):
    def __init__(self, name, uri, sender):
        OpenWithEvolutionAction.__init__(self, name, uri)
        self._sender = sender
        self.set_snippet(name)
        
    def get_icon(self):
        return "stock_mail"
    
    def get_verb(self):
        return (_("From %s") % "<i>%(sender)s</i>" )
    
    def get_name(self, text=None):
        return {"name": self._name, "sender": self._sender}
        
class OpenFeedAction(ShowUrlAction):
    def __init__(self, name, identifier, publisher, snippet=None):
        ShowUrlAction.__init__(self, name, identifier)
        self._publisher = publisher
        self.set_snippet(name)
        
    def get_icon(self):
        return "stock_news"
    
    def get_verb(self):
        return (_("News from %s") % "<i>%(publisher)s</i>" )
    
    def get_name(self, text=None):
        return {"name": self._name, "publisher": self._publisher}

class OpenNoteAction(OpenWithApplicationAction):
    def __init__(self, name, uri, snippet=None):
        OpenWithApplicationAction.__init__(self, name, "tomboy", ["--open-note", uri])
        
    def get_icon(self):
        return "note.png"
    
    def get_verb(self):
        return (_("Note: %s") % "<b>%(name)s</b>")
   
class OpenIMLogAction(OpenWithApplicationAction):
    def __init__(self, name, uri, client, snippet=None):
        OpenWithApplicationAction.__init__(self, name, "beagle-imlogviewer", [])
        self._snippet = snippet
        self._uri = gnomevfs.get_local_path_from_uri(uri)
        self._client = client
        
    def get_icon(self):
        return "im"

    def get_verb(self):
        return (_("With %s") % "<b>%(name)s</b>")
    
    def activate(self, text=None):
        self._arguments = ["--client", self._client, "--highlight-search", text, self._uri]
        OpenWithApplicationAction.activate(self, text)
        
class OpenCalendarAction(OpenWithEvolutionAction):
    def __init__(self, name, uri):
        OpenWithEvolutionAction.__init__(self, name, uri)
        
    def get_icon(self):
        return "stock_calendar"
    
    def get_verb(self):
        return _("Calendar: %s") % "<b>%(name)s</b>"
        
class OpenWebHistoryAction(ShowUrlAction):
    def __init__(self, name, uri, escaped_uri):
        ShowUrlAction.__init__(self, name, uri)
        self.set_snippet(gnomevfs.unescape_string_for_display(escaped_uri))
        
    def get_icon(self):
        return "system-search"
    
    def get_verb(self):
        return _("Open History Item %s") % "<b>%(name)s</b>"
    
class OpenBeagleFileAction(OpenFileAction):
    def __init__(self, name, uri, inside_archive, parent_file):
        self._complete_uri = uri
        self._parent_file = parent_file
        if inside_archive == "true":
            uri = self.__get_archive_uri(uri)
            
        OpenFileAction.__init__(self, name, uri, False)
        
    def __get_archive_uri(self, uri):
        match = re.search("(.+?)#(.+)", uri)
        if match != None:
            return match.groups()[0]
        
    def get_verb(self):
        if self._parent_file != None:
            # translators: in this case the file (2nd) is part of an archive (1st)
            # e.g. README is part of deskbar-applet.tar.gz
            return _("Open %s containing %s") % ("<b>%(parent)s</b>", "<b>%(name)s</b>")
        else:
            return _("Open %s") % "<b>%(name)s</b>"
        
    def get_name(self, text=None):
        names = OpenFileAction.get_name (self)
        if self._parent_file != None:
            names["parent"] = self._parent_file
        return names 
        
    def get_hash(self):
        return self._complete_uri

class BeagleSearchAction(OpenWithApplicationAction):
    def __init__(self, name, term, verb, hit_type=None):
        """
        @param hit_type: Beagle hit type to search for 
        """
        beagle_args = [term]
        if hit_type != None:
            beagle_args.append("type:"+hit_type)
        
    	OpenWithApplicationAction.__init__(self, name, "beagle-search", beagle_args)
    	self._verb = verb

    def get_verb(self):
    	return self._verb
    
### ===== End: Actions ===== ###

class BeagleSearchMatch(deskbar.interfaces.Match):
    def __init__(self, term, cat_type, **args):
    	deskbar.interfaces.Match.__init__(self, name=term, icon="system-search", category=cat_type, **args)
    	verb = _("Additional results for category <b>%s</b>") % _(CATEGORIES[cat_type]['name'])
    	self.term = term
        self.cat_type = cat_type
    	self.add_action( BeagleSearchAction("Beagle Search", term, verb, cat_type) )
    	self.set_priority(self.get_priority()-50)
    
    def get_hash(self, text=None):
    	return "beagle-search %s %s" % (self.term, self.cat_type)
        
class BeagleLiveMatch (deskbar.interfaces.Match):
    
    def __init__(self, result=None, **args):
        """
        result: a dict containing:
            "name" : a name sensible to display for this match
            "uri": the uri of the match as provided by the beagled 'Uri: '-field
            "type": A L{BeagleType} sub-class

        -- and optionally extra fields as provided by the corresponding entry in L{BeagleType.get_extra_properties}.
        """
        deskbar.interfaces.Match.__init__ (self, name=result["name"], **args)
        self.result = result
        
        if not isinstance(result["type"], BeagleType):
            raise TypeError("Expected BeagleType but got %r" % result["type"])
        
        if isinstance(result["type"], ContactType):
            self.add_action( OpenContactAction(result["name"], result["uri"]) )
        elif isinstance(result["type"], MailMessageType):
            self.add_action( OpenMailMessageAction(result["name"], result["uri"], result["sender"]) )
        elif isinstance(result["type"], FeedItemType):
            self.add_action( OpenFeedAction(result["name"], result["identifier"], result["publisher"], result["snippet"]) )
        elif isinstance(result["type"], NoteType):
            self.add_action( OpenNoteAction(result["name"], result["uri"], result["snippet"]) )
        elif isinstance(result["type"], IMLogType):
            self.add_action( OpenIMLogAction(result["name"], result["uri"], result["client"], result["snippet"]) )
        elif isinstance(result["type"], CalendarType):
            self.add_action( OpenCalendarAction(result["name"], result["uri"]) )
        elif isinstance(result["type"], WebHistoryType):
            self.add_action( OpenWebHistoryAction(result["name"], result["uri"], result["escaped_uri"]) )
        elif isinstance(result["type"], FileType):
            # For files inside archives only work with the archive itsself
            result["escaped_uri"] = result["escaped_uri"].split('#')[0]
            # Unescape URI again
            unescaped_uri = gnomevfs.unescape_string_for_display(result["escaped_uri"])
            if not result.has_key("inside_archive"):
                result["inside_archive"] = "false"
            
            if result["inside_archive"] == "true":
                file_open_action = OpenBeagleFileAction(result["name"],
                                                        result["uri"],
                                                        result["inside_archive"],
                                                        result["parent_file"])
            else:
                file_open_action = OpenBeagleFileAction(result["name"],
                                                        result["uri"],
                                                        result["inside_archive"],
                                                        None)
            
            self.add_action(file_open_action, True)
            actions = get_actions_for_uri(unescaped_uri,
                                          display_name=basename(unescaped_uri))
            self.add_all_actions(actions)

        # Load the correct icon
        
        #
        # There is bug http://bugzilla.gnome.org/show_bug.cgi?id=319549
        # which has been fixed and comitted, so we re-enable this snippet
        #
        
        if result["type"] == "File":
            try:
                self.set_icon( result["uri"] )
            except Exception:
                pass
            
        if "snippet" in result and result["snippet"]:
            self.set_snippet (result["snippet"])
    
    def get_hash(self):
        if self.result["type"] == "Contact":
            return self.result["name"]
        if "uri" in self.result:
            return self.result["uri"]
        return deskbar.interfaces.Match.get_hash(self)
    
class BeagleLiveHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': load_icon("system-search"),
            "name": _("Beagle Live"),
            "description": _("Search all of your documents (using Beagle), as you type"),
            'version': VERSION,
            }
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self.__counter_lock = threading.Lock()
        self.__beagle_lock = threading.Lock()
        # We have to store instances for each query term
        self._counter = {} # Count hits for each hit type
        self._at_max = {} # Whether we have reached the maximum for a particular hit type before
        self._beagle_query = {}
        self.__hits_added_id = {}
        self.__hits_finished_id = {}
        
    def initialize (self):
        self.beagle = beagle.Client()
        
    def stop(self):
        self.beagle = None
   
    def query (self, qstring):
        self.__counter_lock.acquire()
        self._counter[qstring] = {}
        self._at_max[qstring] = {}
        self.__counter_lock.release()
        
        try:
            self.__beagle_lock.acquire()
            
            beagle_query = beagle.Query()
            self.__hits_added_id[qstring]= beagle_query.connect ("hits-added", self._on_hits_added, qstring)
            self.__hits_finished_id[qstring] = beagle_query.connect ("finished", self._on_finished, qstring)
            beagle_query.add_text (qstring)
            
            self._beagle_query[qstring] = beagle_query
       
            LOGGER.debug ("Sending beagle query (%r) for '%s'", self._beagle_query[qstring], qstring)
            try:
                self.beagle.send_request_async (self._beagle_query[qstring])
            except GError, e:
                LOGGER.exception(e)
                self._cleanup_query(qstring)
        finally:
            self.__beagle_lock.release()
               
    def _on_hits_added (self, query, response, qstring):
        hit_matches = []
        for hit in response.get_hits():
            if hit.get_type() not in TYPES:
                LOGGER.info("Beagle live seen an unknown type: %s", str(hit.get_type()))
                continue
                
            match = self._create_match(query, hit, qstring)
            if match != None:
                hit_matches.append(match)
        
        self._emit_query_ready (qstring, hit_matches)
            
    def _on_finished (self, query, response, qstring):
        LOGGER.debug ("Beagle query (%r) for '%s' finished with response %r", query, qstring, response)
        
        self._cleanup_query(qstring)
        
        self.__counter_lock.acquire()
        if qstring in self._counter:
            del self._counter[qstring]
            del self._at_max[qstring]
        self.__counter_lock.release()
        
    def _cleanup_query(self, qstring):
        # Remove counter for query
        self.__beagle_lock.acquire()
        # Disconnect signals, otherwise we receive late matches
        # when beagle found the query term in a newly indexed file
        beagle_query = self._beagle_query[qstring]
        beagle_query.disconnect (self.__hits_added_id[qstring])
        beagle_query.disconnect (self.__hits_finished_id[qstring])
        del self._beagle_query[qstring]
        del self.__hits_added_id[qstring]
        del self.__hits_finished_id[qstring]
        self.__beagle_lock.release()
        
    def _get_snippet (self, query, hit):
        snippet_request = beagle.SnippetRequest()
        snippet_request.set_query(query)
        snippet_request.set_hit(hit)
        
        try:
            self.__beagle_lock.acquire()
            try:
                response = self.beagle.send_request (snippet_request)
            except GError, e:
                LOGGER.exception(e)
                response = None
        finally:
            self.__beagle_lock.release()
        
        if response == None:
            return None
        
        snippet = response.get_snippet()
        # Older versions of beagle return None
        # if an error occured during snippet retrival 
        if snippet != None:
            # Remove trailing whitespaces and escape '%'
            snippet = snippet.strip().replace("%", "%%")
         
        return snippet
    
    def _get_beagle_type(self, hit_type):
        if hit_type in TYPES:
            return TYPES[hit_type]
        else:
            LOGGER.warning("Unknown beagle match type found: %s", result["type"] )
            return None
            
    def _create_match(self, query, hit, qstring):
        hit_type = hit.get_type()
        snippet = None
        
        beagle_type = self._get_beagle_type(hit_type)
        if beagle_type == None:
            return None
        
        # Directories are Files in beagle context
        if hit_type == "File":
            filetype = hit.get_properties("beagle:FileType")
            if filetype != None \
                and filetype[0] in BEAGLE_FILE_TYPE_TO_TYPES_MAP:
                beagle_type = TYPES[BEAGLE_FILE_TYPE_TO_TYPES_MAP[filetype[0]]]
        
        if beagle_type.get_has_snippet():
            snippet = self._get_snippet(query, hit)
        
        result = {
            "uri":  hit.get_uri(),
            "type": beagle_type,
            "snippet": snippet,
        }
        
        # Get category
        cat_type = beagle_type.get_category()
        
        self.__counter_lock.acquire()
        # Create new counter for query and type 
        if not cat_type in self._counter[qstring]:
            self._counter[qstring][cat_type] = 0
        # Increase counter
        self._counter[qstring][cat_type] += 1

        if self._counter[qstring][cat_type] > MAX_RESULTS:
            if cat_type in self._at_max[qstring]:
                # We already reached the maximum before
                match = None
            else:
                # We reach the maximum for the first time
                self._at_max[qstring][cat_type] = True
                match = BeagleSearchMatch(qstring, cat_type) 
            self.__counter_lock.release()
            return match
        self.__counter_lock.release()
    
        self._get_properties(hit, result)
        self._escape_pango_markup(result, qstring)
        
        return BeagleLiveMatch(result, category=cat_type, priority=self.get_priority())
        
    def _get_properties(self, hit, result):
        beagle_type = result["type"]
          
        name = None
        for prop in beagle_type.get_name_properties():
            try:
                name = hit.get_properties(prop)[0] # get_property_one() would be cleaner, but this works around bug #330053
            except:
                pass
                    
            if name != None:
                result["name"] = name
                break
        
        if name == None:
            #translators: This is used for unknown values returned by beagle
            #translators: for example unknown email sender, or unknown note title
            result["name"] = _("?")
        
        for prop, keys in beagle_type.get_extra_properties().items():
            val = None
            for key in keys:
                try:
                    val = hit.get_properties(key)[0] # get_property_one() would be cleaner, but this works around bug #330053
                except:
                    pass
                        
                if val != None:
                    result[prop] = val
                    break
                
            if val == None:
                #translators: This is used for unknown values returned by beagle
                #translators: for example unknown email sender, or unknown note title
                result[prop] = _("?")
    
    def _escape_pango_markup(self, result, qstring):
        """
        Escape everything for display through pango markup, except filenames.
        Filenames are escaped in escaped_uri or escaped_identifier
        """
        for key, val in result.items():
            if key == "uri" or key == "identifier":
                result["escaped_"+key] = cgi.escape(val)
            elif key == "snippet":
                # Add the snippet, in escaped form if available
                if result["snippet"] != None and result["snippet"] != "":
                    tmp = re.sub(r"<.*?>", "", result["snippet"])
                    tmp = re.sub(r"</.*?>", "", tmp)
                    result["snippet"] = cgi.escape(tmp)
                    
                    result["snippet"] = re.sub(re.escape(qstring), "<span weight='bold'>"+qstring+"</span>", result["snippet"], re.IGNORECASE)
                else:
                    result["snippet"] = ""
            elif isinstance(result[key], str):
                result[key] = cgi.escape(val)
        
    @staticmethod
    def has_requirements():
        # Check if we have python bindings for beagle
        try:
            import beagle
        except Exception, e:
            BeagleLiveHandler.INSTRUCTIONS = _("Could not load beagle, libbeagle has been compiled without python bindings.")
            return False
    
        # Check if beagled is running        
        if not beagle.beagle_util_daemon_is_running ():
            if is_program_in_path("beagled"):
                BeagleLiveHandler.INSTRUCTIONS = _("Beagle daemon is not running.")
                return False
            else:
                BeagleLiveHandler.INSTRUCTIONS = _("Beagled could not be found in your $PATH.")
                return False
        else:
            return True
