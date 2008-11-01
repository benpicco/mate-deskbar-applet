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
import cgi
import re
import deskbar, deskbar.interfaces.Module
import deskbar.interfaces.Match
import gio
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
    
    def __init__(self, hit_type):
        """
        @param hit_type: The hit type from beagle.
        This is used by L{BeagleSearchMatch}.
        It's appended to the beagle-search call to search
        for this particular type only
        """
        self.__name_properties = []
        self.__extra_properties = {}
        self.__category = "default"
        self.__snippet = False
        self.__hit_type = hit_type
    
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
    
    def get_hit_type(self):
        return self.__hit_type
    
class ContactType(BeagleType):
    
    def __init__(self, hit_type):
        BeagleType.__init__(self, hit_type)
        self.set_name_properties(("fixme:FileAs",))
        self.set_category("people")
        
class MailMessageType(BeagleType):
    
    def __init__(self, hit_type):
        BeagleType.__init__(self, hit_type)
        self.set_name_properties(("dc:title",
                                  "parent:dc:title",))
        self.set_extra_properties({"sender": ("fixme:from_name",
                                              "parent:fixme:from_name",
                                              "fixme:from",),
                                   "client": ("fixme:client",),
                                   "thunderbird-uri": ("fixme:uri",) 
        })
        self.set_category("emails")
        
class FileType(BeagleType):
    
    def __init__(self, hit_type):
        BeagleType.__init__(self, hit_type)
        self.set_name_properties(("beagle:ExactFilename",))
        self.set_extra_properties({"inside_archive": ("fixme:inside_archive",),
                                   "parent_file": ("parent:beagle:ExactFilename",)
                                  })
        self.set_category("files")
        self.set_has_snippet(True)
 
class DirectoryType(FileType):
    
    def __init__(self, hit_type):
        FileType.__init__(self, hit_type)
        self.set_category("places")
        self.set_has_snippet(False)

class DocumentType(FileType):
    
    def __init__(self, hit_type):
        FileType.__init__(self, hit_type)
        self.set_category("documents")
        
class AudioType(FileType):
    
    def __init__(self, hit_type):
        FileType.__init__(self, hit_type)
        self.set_category("audio")
        self.set_has_snippet(False)
        
class VideoType(FileType):
    
    def __init__(self, hit_type):
        FileType.__init__(self, hit_type)
        self.set_category("video")
        self.set_has_snippet(False)
        
class ImageType(FileType):
    
    def __init__(self, hit_type):
        FileType.__init__(self, hit_type)
        self.set_category("images")
        self.set_has_snippet(False)
    
class FeedItemType(BeagleType):
    
    def __init__(self, hit_type):
        BeagleType.__init__(self, hit_type)
        self.set_name_properties(("dc:title",))
        self.set_extra_properties({"publisher": ("dc:publisher",),
                                   "identifier": ("dc:identifier",)
                                   })
        self.set_category("news")
        
class NoteType(BeagleType):
    
    def __init__(self, hit_type):
        BeagleType.__init__(self, hit_type)
        self.set_name_properties(("dc:title",))
        self.set_category("notes")
        self.set_has_snippet(True)
        
class IMLogType(BeagleType):
    
    def __init__(self, hit_type):
        BeagleType.__init__(self, hit_type)
        self.set_name_properties(("fixme:speakingto",))
        self.set_extra_properties({"client": ("fixme:client",)})
        self.set_category("conversations")
        self.set_has_snippet(True)
    
class CalendarType(BeagleType):
    
    def __init__(self, hit_type):
        BeagleType.__init__(self, hit_type)
        self.set_name_properties(("fixme:summary",))
        self.set_category("documents")
        
class WebHistoryType(BeagleType):
    
    def __init__(self, hit_type):
        BeagleType.__init__(self, hit_type)
        # FIX-BEAGLE bug #330053, dc:title returns as None even though it _is_ set
        self.set_name_properties(("dc:title",))
        self.set_category("web")
        self.set_has_snippet(True)
        
# We use keyword:beagle:xxx instead of type:xxx here,
# because beagle-search expects that the value of type
# in the user's locale language. Using this hack we
# can always use English
TYPES = {
    "Contact": ContactType("keyword:beagle:HitType=Contact"),
    "MailMessage": MailMessageType("keyword:beagle:HitType=MailMessage"),
    "File": FileType("keyword:beagle:HitType=File"),
    "Directory": DirectoryType("keyword:beagle:FileType=folder"),
    "Document": DocumentType("keyword:beagle:FileType=document"),
    "Audio": AudioType("keyword:beagle:FileType=audio"),
    "Video": VideoType("keyword:beagle:FileType=video"),
    "Image": ImageType("keyword:beagle:FileType=image"), 
    "FeedItem": FeedItemType("keyword:beagle:HitType=FeedItem"),
    "Note": NoteType("keyword:beagle:HitType=Note"),
    "IMLog": IMLogType("keyword:beagle:HitType=IMLog"),
    "Calendar": CalendarType("keyword:beagle:HitType=Calendar"),
    "WebHistory": WebHistoryType("keyword:beagle:HitType=WebHistory"),
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
    def __init__(self, name, uri, sender=None):
        OpenWithEvolutionAction.__init__(self, name, uri)
        
    def get_icon(self):
        return "stock_mail"
    
    def get_verb(self):
        return "<b>%(name)s</b>"
    
class OpenThunderbirdMailMessageAction(OpenWithApplicationAction):
    def __init__(self, name, uri):
        OpenWithApplicationAction.__init__(self, name, "thunderbird",
                                               ["-viewbeagle", uri])
    
    def get_icon(self):
        return "stock_mail"
    
    def get_verb(self):
        return "<b>%(name)s</b>"
        
class OpenFeedAction(ShowUrlAction):
    def __init__(self, name, identifier, publisher=None, snippet=None):
        ShowUrlAction.__init__(self, name, identifier)
        
    def get_icon(self):
        return "stock_news"
    
    def get_verb(self):
        return "<b>%(name)s</b>"
    
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
        self._uri = gio.File(uri=uri).get_path ()
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
        self._display_uri = gio.File (uri=escaped_uri).get_parse_name()
        
    def get_icon(self):
        return "system-search"
    
    def get_verb(self):
        return _("Open History Item %s") % "<b>%(name)s</b>"
    
    def get_name(self, text=None):
        return ShowUrlAction.get_name(self, text=None)
        
    def get_tooltip(self, text=None):
        return self._display_uri
    
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
        if hasattr(self, "_parent_file") and self._parent_file != None:
            # translators: in this case the file (2nd) is part of an archive (1st)
            # e.g. README is part of deskbar-applet.tar.gz
            return _("Open %s containing %s") % ("<b>%(parent)s</b>", "<b>%(name)s</b>")
        else:
            return _("Open %s") % "<b>%(name)s</b>"
        
    def get_name(self, text=None):
        names = OpenFileAction.get_name (self)
        if hasattr(self, "_parent_file") and self._parent_file != None:
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
            beagle_args.append(hit_type)
        
    	OpenWithApplicationAction.__init__(self, name, "beagle-search", beagle_args)
    	self._verb = verb

    def get_verb(self):
    	return self._verb
    
### ===== End: Actions ===== ###

class BeagleSearchMatch(deskbar.interfaces.Match):
    def __init__(self, term, cat_type, hit_type, **args):
    	deskbar.interfaces.Match.__init__(self, name=term, icon="system-search", category=cat_type, **args)
    	# Prevent xgettext from extracting "name" key
    	cat_name = CATEGORIES[cat_type]['name']
     	verb = _("Additional results for category <b>%s</b>") % _(cat_name)
    	self.term = term
        self.cat_type = cat_type
    	self.add_action( BeagleSearchAction("Beagle Search", term, verb, hit_type) )
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
            if result["client"] == "thunderbird":
                action = OpenThunderbirdMailMessageAction(result["name"], result["thunderbird-uri"])
            elif result["client"] == "evolution":
                 action = OpenMailMessageAction(result["name"], result["uri"])
            else:
                LOGGER.warning("Unknown/Unsupported e-mail client %s", result["client"])
                return
            self.add_action( action )
            self.set_snippet( _("From <i>%s</i>") % result["sender"] )
        elif isinstance(result["type"], FeedItemType):
            self.add_action( OpenFeedAction(result["name"], result["identifier"]) )
            self.set_snippet( _("From <i>%s</i>") % result["publisher"] )
        elif isinstance(result["type"], NoteType):
            self.add_action( OpenNoteAction(result["name"], result["uri"]) )
        elif isinstance(result["type"], IMLogType):
            self.add_action( OpenIMLogAction(result["name"], result["uri"], result["client"]) )
        elif isinstance(result["type"], CalendarType):
            self.add_action( OpenCalendarAction(result["name"], result["uri"]) )
        elif isinstance(result["type"], WebHistoryType):
            self.add_action( OpenWebHistoryAction(result["name"], result["uri"], result["escaped_uri"]) )
        elif isinstance(result["type"], FileType):
            # For files inside archives only work with the archive itsself
            result["escaped_uri"] = result["escaped_uri"].split('#')[0]
            # Unescape URI again
            unescaped_uri = gio.File(uri=result["escaped_uri"]).get_parse_name()
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
        self.__snippet_lock = threading.Lock()
        self.__finished_lock = threading.Lock()
        
        self.__snippet_request = {} # Maps beagle.Hit to beagle.SnippetRequest
        
        # We have to store instances for each query term
        self._counter = {} # Count hits for each hit type
        self._at_max = {} # Whether we have reached the maximum for a particular hit type before
        self._beagle_query = {}
        self.__hits_added_id = {}
        self.__hits_finished_id = {}
        self.__finished = {} # Whether we got all matches from beagle for query
        
    def initialize (self):
        self.beagle = beagle.Client()
        
    def stop(self):
        self.beagle = None
   
    def query (self, qstring):
        self.__counter_lock.acquire()
        self._counter[qstring] = {}
        self._at_max[qstring] = {}
        self.__counter_lock.release()
        
        self.__finished_lock.acquire()
        self.__finished[qstring] = False
        self.__finished_lock.release()
        
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
        for hit in response.get_hits():
            if hit.get_type() not in TYPES:
                LOGGER.info("Beagle live seen an unknown type: %s", str(hit.get_type()))
                continue
            
            beagle_type = self._get_beagle_type(hit)
            if beagle_type == None:
                continue
            
            if beagle_type.get_has_snippet():
                self._get_snippet(query, hit, qstring, beagle_type)
            else:
                self._create_match(hit, beagle_type, qstring)
            
    def _on_finished (self, query, response, qstring):
        LOGGER.debug ("Beagle query (%r) for '%s' finished with response %r", query, qstring, response)
        self.__finished_lock.acquire()
        self.__finished[qstring] = True
        self.__finished_lock.release()
        
    def _on_snippet_received(self, request, response, hit, qstring, beagle_type):
        snippet = response.get_snippet()
        if snippet == None:
            snippet_text = None
        else:
            # Remove trailing whitespaces and escape '%'
            snippet_text = snippet.strip().replace("%", "%%")
            
        self._create_match(hit, beagle_type, qstring, snippet_text)
    
    def _on_snippet_closed(self, request, hit, qstring):
        self._cleanup_snippet(hit)
        
        self.__snippet_lock.acquire()
        n_snippets = len(self.__snippet_request)
        self.__snippet_lock.release()
        
        self.__finished_lock.acquire()
        finished = self.__finished[qstring]
        self.__finished_lock.release()
        
        # FIXME: This only works when at least one
        # result has a snippet, otherwise we
        # miss cleaning up
        if finished and n_snippets == 0:
            self._cleanup_query(qstring)
            self._cleanup_counter(qstring)
            
    def _cleanup_counter(self, qstring):
        self.__counter_lock.acquire()
        if qstring in self._counter:
            del self._counter[qstring]
            del self._at_max[qstring]
        self.__counter_lock.release()
        
    def _cleanup_snippet(self, hit):
        LOGGER.debug("Cleaning up hit %r", hit)
        self.__snippet_lock.acquire()
        del self.__snippet_request[hit]
        self.__snippet_lock.release()
        hit.unref()
               
    def _cleanup_query(self, qstring):
        LOGGER.debug("Cleaning up query for '%s'", qstring)
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
        
        self.__finished_lock.acquire()
        del self.__finished[qstring]
        self.__finished_lock.release()
        
    def _get_snippet (self, query, hit, qstring, beagle_type):
        LOGGER.debug("Retrieving snippet for hit %r", hit)
        
        snippet_request = beagle.SnippetRequest()
        snippet_request.set_query(query)
        snippet_request.set_hit(hit)
        hit.ref()
        snippet_request.connect('response', self._on_snippet_received, hit, qstring, beagle_type)
        snippet_request.connect('closed', self._on_snippet_closed, hit, qstring)
        
        self.__snippet_lock.acquire()
        self.__snippet_request[hit] = snippet_request
        self.__snippet_lock.release()
        
        try:
            self.__beagle_lock.acquire()
            try:
                self.beagle.send_request_async (snippet_request)
            except GError, e:
                LOGGER.exception(e)
                self._cleanup_snippet(hit)
        finally:
            self.__beagle_lock.release()
    
    def _get_beagle_type(self, hit):
        """
        Returns the appropriate L{BeagleType}
        for the given hit
        
        @type hit: beagle.Hit
        @return: L{BeagleType} instance
        """
        hit_type = hit.get_type()
        snippet = None
        
        if hit_type in TYPES:
            beagle_type = TYPES[hit_type]
        else:
            LOGGER.warning("Unknown beagle match type found: %s", result["type"] )
            return None
        
        # Directories are Files in beagle context
        if hit_type == "File":
            filetype = hit.get_properties("beagle:FileType")
            if filetype != None \
                and filetype[0] in BEAGLE_FILE_TYPE_TO_TYPES_MAP:
                beagle_type = TYPES[BEAGLE_FILE_TYPE_TO_TYPES_MAP[filetype[0]]]
                
        return beagle_type
           
    def _create_match(self, hit, beagle_type, qstring, snippet=None):
        # Get category
        cat_type = beagle_type.get_category()
        
        result = {
            "uri":  hit.get_uri(),
            "type": beagle_type,
            "snippet": snippet,
        }
        
        self.__counter_lock.acquire()
        # Create new counter for query and type 
        if not cat_type in self._counter[qstring]:
            self._counter[qstring][cat_type] = 0
        # Increase counter
        self._counter[qstring][cat_type] += 1

        if self._counter[qstring][cat_type] > MAX_RESULTS:
            if cat_type in self._at_max[qstring]:
                # We already reached the maximum before
                self.__counter_lock.release()
                return
            else:
                # We reach the maximum for the first time
                self._at_max[qstring][cat_type] = True
                self._emit_query_ready(qstring,
                                       [BeagleSearchMatch(qstring,
                                                          cat_type,
                                                          beagle_type.get_hit_type())]) 
            self.__counter_lock.release()
            return
        self.__counter_lock.release()
    
        self._get_properties(hit, result)
        self._escape_pango_markup(result, qstring)
        
        self._emit_query_ready(qstring,
                               [BeagleLiveMatch(result,
                                                category=cat_type,
                                                priority=self.get_priority())])
        
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
                    
                    # FIXME: re.escape too much, we only want to escape special regex chars
                    # we should provide a convenient method for _all_ modules
                    result["snippet"] = re.sub(re.escape(qstring),
                                               "<span weight='bold'>"+qstring+"</span>",
                                               result["snippet"],
                                               re.IGNORECASE)
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
