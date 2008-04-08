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

# The TYPES dict contains Beagle HitTypes as keys with
# templates for the valid fields.
#
# A Hit Type consists of:
#    "name"        : Template used to find a user-displayable name
#
# Optionally:
#    "extra"    : A dict containing key:template pairs to search for. You can use %(key)s in "description".
#
# Note:
#  The templates are a tuple of strings which should be tested in order to retreive the beagle property

TYPES = {
    "Contact"    : {
        "name"    : ("fixme:FileAs",),
        "category": "people",
        },
    
    "MailMessage"     : {
        "name"    :("dc:title", "parent:dc:title"),
        "extra": {"sender":("fixme:from_name", "parent:fixme:from_name")},
        "category": "emails",
        },
    "File"         : {
        "name"    : ("beagle:ExactFilename",),
        "extra" : {"inside_archive": ("fixme:inside_archive",), "parent_file": ("parent:beagle:ExactFilename",) },
        "category": "files",
        "snippet": True,
        },
    "Directory"    : {
        "name"    : ("beagle:ExactFilename",),
        "category": "places",
        },
    "FeedItem"    : {
        "name"    : ("dc:title",),
        "category": "news",
        "snippet": True,
        "extra": {"publisher":("dc:publisher",), "identifier": ("dc:identifier",)},
        },
    "Note"        : {
        "name"    : ("dc:title",),
        "snippet": True,
        "category": "notes",
        },
    "IMLog"        : {
        "name"    : ("fixme:speakingto",),
        "extra" : {"client": ("fixme:client",)},
        "snippet": True,
        "category": "conversations",
        },
    "Calendar"    : {
        "name"    : ("fixme:summary",),
        "category": "documents",
        },
    "WebHistory": {
        "name"    : ("dc:title",), # FIX-BEAGLE bug #330053, dc:title returns as None even though it _is_ set
        "category": "web",
        },
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
        
    def get_icon(self):
        return "stock_mail"
    
    def get_verb(self):
        return (_("From %s") % "<i>%(sender)s</i>" ) + "\n<b>%(name)s</b>"
    
    def get_name(self, text=None):
        return {"name": self._name, "sender": self._sender}
        
class OpenFeedAction(ShowUrlAction):
    def __init__(self, name, identifier, publisher, snippet=None):
        ShowUrlAction.__init__(self, name, identifier)
        self._publisher = publisher
        
    def get_icon(self):
        return "stock_news"
    
    def get_verb(self):
        return (_("News from %s") % "<i>%(publisher)s</i>" ) + "\n<b>%(name)s</b>"
    
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
        self._escaped_uri = gnomevfs.unescape_string_for_display(escaped_uri)
        
    def get_icon(self):
        return "system-search"
    
    def get_verb(self):
        verb = _("Open History Item %s") % "<b>%(name)s</b>" 
        verb += "\n<span size='small'>%s</span>" % self._escaped_uri
        return verb
    
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
    def __init__(self, name, term, verb):
    	OpenWithApplicationAction.__init__(self, name, "beagle-search", [term])
    	self._verb = verb

    def get_verb(self):
    	return self._verb
    
### ===== End: Actions ===== ###

class BeagleSearchMatch(deskbar.interfaces.Match):
    def __init__(self, term, cat_type, **args):
    	deskbar.interfaces.Match.__init__(self, name=term, icon= "system-search", category=cat_type, **args)
    	verb = _("Additional results for category <b>%s</b>") % _(CATEGORIES[cat_type]['name'])
    	self.term = term
    	self.add_action( BeagleSearchAction("Beagle Search", term, verb) )
    	self.set_priority(self.get_priority()-50)
    
    def get_hash(self, text=None):
    	return "beagle-search "+self.term
        
class BeagleLiveMatch (deskbar.interfaces.Match):
    def __init__(self, result=None, **args):
        """
        result: a dict containing:
            "name" : a name sensible to display for this match
            "uri": the uri of the match as provided by the beagled 'Uri: '-field
            "type": One of the types listed in the TYPES dict
            "source": Which beagle indexer found that result

        -- and optionally extra fields as provided by the corresponding entry in TYPES.
        Fx. "MailMessage". has an extra "sender" entry.
        """
        deskbar.interfaces.Match.__init__ (self, name=result["name"], **args)
        self.result = result
        
        if (result["type"] == "Contact"):
            self.add_action( OpenContactAction(result["name"], result["uri"]) )
        elif (result["type"] == "MailMessage"):
            self.add_action( OpenMailMessageAction(result["name"], result["uri"], result["sender"]) )
        elif (result["type"] == "FeedItem"):
            self.add_action( OpenFeedAction(result["name"], result["identifier"], result["publisher"], result["snippet"]) )
        elif (result["type"] == "Note"):
            self.add_action( OpenNoteAction(result["name"], result["uri"], result["snippet"]) )
        elif (result["type"] == "IMLog"):
            self.add_action( OpenIMLogAction(result["name"], result["uri"], result["client"], result["snippet"]) )
        elif (result["type"] == "Calendar"):
            self.add_action( OpenCalendarAction(result["name"], result["uri"]) )
        elif (result["type"] == "WebHistory"):
            self.add_action( OpenWebHistoryAction(result["name"], result["uri"], result["escaped_uri"]) )
        elif (result["type"] == "File" or result["type"] == "Directory"):
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
                
            actions = [file_open_action] \
                       + get_actions_for_uri( unescaped_uri,
                                              display_name=basename(unescaped_uri)
                                            )
            self.add_all_actions( actions )
        else:
            LOGGER.warning("Unknown beagle match type found: %s", result["type"] )

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
        self._counter = {}
        self._beagle_query = {}
        self.__hits_added_id = {}
        self.__hits_finished_id = {}
        
    def initialize (self):
        self.beagle = beagle.Client()
   
    def query (self, qstring):
        self._counter[qstring] = {}
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
            
            snippet = None
            if "snippet" in TYPES[hit.get_type()] and TYPES[hit.get_type()]["snippet"]:
                snippet = self._get_snippet(query, hit)
                
            match = self._create_match(query, hit, qstring, snippet)
            if match != None:
                hit_matches.append(match)
        
        self._emit_query_ready (qstring, hit_matches)
            
    def _on_finished (self, query, response, qstring):
        LOGGER.debug ("Beagle query (%r) for '%s' finished with response %r", query, qstring, response)
        
        self._cleanup_query(qstring)
        
        self.__counter_lock.acquire()
        if qstring in self._counter:
            del self._counter[qstring]
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
            
    def _create_match(self, query, hit, qstring, snippet=None):
        hit_type = hit.get_type()
        
        # Directories are Files in beagle context
        if hit_type == "File":
            filetype = hit.get_properties("beagle:FileType")
            if filetype != None and filetype[0] == 'directory':
                hit_type = "Directory"
        
        self.__counter_lock.acquire()
        # Create new counter for query and type 
        if not hit_type in self._counter[qstring]:
            self._counter[qstring][hit_type] = 0
        # Increase counter
        self._counter[qstring][hit.get_type()] += 1

        if self._counter[qstring][hit_type] > MAX_RESULTS:
            self.__counter_lock.release()
            return None
        self.__counter_lock.release()
                 
        result = {
            "uri":  hit.get_uri(),
            "type": hit_type,
            "snippet": snippet,
        }
        
        # Get category
        if TYPES.has_key(result["type"]):
            cat_type = TYPES[result["type"]]["category"]
        else:
            cat_type = "default"
            
        self._get_properties(hit, result)
        self._escape_pango_markup(result, qstring)
        
        return BeagleLiveMatch(result, category=cat_type, priority=self.get_priority())
        
    def _get_properties(self, hit, result):
        hit_type_data = TYPES[hit.get_type()]
          
        name = None
        for prop in hit_type_data["name"]:
            name = hit.get_properties(prop)[0] # get_property_one() would be cleaner, but this works around bug #330053
                    
            if name != None:
                result["name"] = name
                break
        
        if name == None:
            #translators: This is used for unknown values returned by beagle
            #translators: for example unknown email sender, or unknown note title
            result["name"] = _("?")
            
        if "extra" in hit_type_data:
            for prop, keys in hit_type_data["extra"].items():
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
            else:
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
