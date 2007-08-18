from deskbar.core.Utils import is_program_in_path, load_icon
from deskbar.defs import VERSION
from deskbar.handlers.actions.ActionsFactory import get_actions_for_uri
from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from deskbar.handlers.actions.OpenFileAction import OpenFileAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from os.path import basename
import cgi, re
import deskbar, deskbar.interfaces.Module
import deskbar.interfaces.Match
import gtk, gnome.ui, gnomevfs
import logging

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
        "category": "files",
        "snippet": True,
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
    def __init__(self, name, identifier, publisher, snippet):
        ShowUrlAction.__init__(self, name, identifier)
        self._publisher = publisher
        self._snippet = snippet
        
    def get_icon(self):
        return "stock_news"
    
    def get_verb(self):
        return (_("News from %s") % "<i>%(publisher)s</i>" ) + "\n<b>%(name)s</b>" + self._snippet
    
    def get_name(self, text=None):
        return {"name": self._name, "publisher": self._publisher}

class OpenNoteAction(OpenWithApplicationAction):
    def __init__(self, name, uri, snippet):
        OpenWithApplicationAction.__init__(self, name, "tomboy", ["--open-note", uri])
        self._snippet = snippet
        
    def get_icon(self):
        return "stock_notes"
    
    def get_verb(self):
        return (_("Note: %s") % "<b>%(name)s</b>") + self._snippet
   
class OpenIMLogAction(OpenWithApplicationAction):
    def __init__(self, name, uri, client, snippet):
        OpenWithApplicationAction.__init__(self, name, "beagle-imlogviewer", [])
        self._snippet = snippet
        self._uri = gnomevfs.get_local_path_from_uri(uri)
        self._client = client
        
    def get_icon(self):
        return "im"

    def get_verb(self):
        return _("With %s") % "<b>%(name)s</b>%(snippet)s"

    def get_name(self, text=None):
        return {"name": self._name, "snippet": self._snippet}
    
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
        self._escaped_uri = escaped_uri
        
    def get_icon(self):
        return "system-search"
    
    def get_verb(self):
        return (_("Open History Item %s") % "<i>%(name)s</i>") + "\n%(escaped_uri)s"
    
    def get_name(self, text=None):
        return {"name": self._name, "escaped_uri": self._escaped_uri}

### ===== End: Actions ===== ###
        
class BeagleLiveMatch (deskbar.interfaces.Match):
    def __init__(self, result=None, **args):
        """
        result: a dict containing:
            "name" : a name sensible to display for this match
            "uri": the uri of the match as provided by the beagled 'Uri: '-field
            "type": One of the types listed in the TYPES dict

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
        elif (result["type"] == "File"):
            # Unescape URI again
            unescaped_uri = gnomevfs.unescape_string_for_display(result["escaped_uri"])
            actions = [OpenFileAction(result["name"], result["uri"], False)] + get_actions_for_uri(
                                    unescaped_uri,
                                    display_name=basename(unescaped_uri))
            self.add_all_actions( actions )
        else:
            logging.warning("Unknown beagle match type found: "+result["type"] )

        # Load the correct icon
        
        #
        # There is bug http://bugzilla.gnome.org/show_bug.cgi?id=319549
        # which has been fixed and comitted, so we re-enable this snippet
        #
        
        if result["type"] == "File":
            try:
                self._icon = result["uri"]
            except Exception:
                pass
    
    def get_hash(self, text=None):
        if "uri" in self.result:
            return self.result["uri"]
        
    def get_name(self, text=None):
        return self._name + self.result["snippet"]
        
class SnippetContainer:
    def __init__(self, hit):
        self.hit = hit
        self.snippet = None
    
class BeagleLiveHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': load_icon("system-search"),
            "name": _("Beagle Live"),
            "description": _("Search all of your documents (using Beagle), as you type"),
            'version': VERSION,
            }
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self.counter = {}
        self.snippets = {}
        
    def initialize (self):
        self.beagle = beagle.Client()
        
    def query (self, qstring):
        beagle_query = beagle.Query()
        beagle_query.add_text(qstring)
        beagle_query.connect("hits-added", self.hits_added, qstring, MAX_RESULTS)
        try:
            self.beagle.send_request_async(beagle_query)
        except:
            return
            
        self.counter[qstring] = {}
    
    def has_config(self):
        return True
        
    def _on_snippet_received(self, request, response, query, container, qstring, qmax):
        container.snippet = response.get_snippet()
        self._on_hit_added(query, container, qstring, qmax)
    
    def _on_snippet_closed(self, request, query, container, qstring, qmax):
        if container.snippet == None:
            self._on_hit_added(query, container, qstring, qmax)
            
        container.hit.unref()
            
    def _on_hit_added(self, query, hit, qstring, qmax):
        fire_signal = False
        snippet = None
        
        if hit.__class__ == SnippetContainer:
            hit, snippet = hit.hit, hit.snippet
            fire_signal = True
            
        if not hit.get_type() in self.counter[qstring]:
            self.counter[qstring][hit.get_type()] = 0

        if self.counter[qstring][hit.get_type()] >= qmax:
            return
            
        hit_type = TYPES[hit.get_type()]
        result = {
            "uri":  hit.get_uri(),
            "type": hit.get_type(),
        }
            
        name = None
        for prop in hit_type["name"]:
            try:
                name = hit.get_properties(prop)[0] # get_property_one() would be cleaner, but this works around bug #330053
            except:
                try:
                    # Beagle < 0.2
                    name = hit.get_property(prop)
                except:
                    pass
                    
            if name != None:
                result["name"] = name
                break
        
        if name == None:
            #translators: This is used for unknown values returned by beagle
            #translators: for example unknown email sender, or unknown note title
            result["name"] = _("?")
            
        if "extra" in hit_type:
            for prop, keys in hit_type["extra"].items():
                val = None
                for key in keys:
                    try:
                        val = hit.get_properties(key)[0] # get_property_one() would be cleaner, but this works around bug #330053
                    except:
                        try:
                            # Beagle < 0.2
                            val = hit.get_property(key)
                        except:
                            pass
                            
                    if val != None:
                        result[prop] = val
                        break
                    
                if val == None:
                    #translators: This is used for unknown values returned by beagle
                    #translators: for example unknown email sender, or unknown note title
                    result[prop] = _("?")
        
        # Escape everything for display through pango markup, except filenames. Filenames are escaped in escaped_uri or 
        # escaped_identifier
        for key, val in result.items():
            if key == "uri" or key == "identifier":
                result["escaped_"+key] = cgi.escape(val)
            else:
                result[key] = cgi.escape(val)
        
        # Add the snippet, in escaped form if available
        if snippet != None:
            tmp = re.sub(r"<.*?>", "", snippet)
            tmp = re.sub(r"</.*?>", "", tmp)
            result["snippet"] = "\n<span size='small'>%s</span>" % cgi.escape(tmp)
            #tmp = re.sub('<font color="', '<span foreground="', snippet)
            #tmp = re.sub('</font>', '</span>', tmp)
            #print tmp
            #result["snippet"] = "\n"+tmp
        else:
            result["snippet"] = ""
            
        self.counter[qstring][hit.get_type()] = self.counter[qstring][hit.get_type()] +1

        if TYPES.has_key(result["type"]):
            cat_type = TYPES[result["type"]]["category"]
        else:
            cat_type = "default"
        
        match = BeagleLiveMatch(result, category=cat_type, priority=self.get_priority())
        
        if fire_signal:
            self._emit_query_ready(qstring, [match])
        else:    
            return match
        
    def hits_added(self, query, response, qstring, qmax):
        hit_matches = []
        for hit in response.get_hits():
            if hit.get_type() not in TYPES:
                logging.warning("Beagle live seen an unknown type:"+ hit.get_type())
                continue
            
            if "snippet" in TYPES[hit.get_type()] and TYPES[hit.get_type()]["snippet"]:
                req = beagle.SnippetRequest()
                req.set_query(query)
                req.set_hit(hit)
                container = SnippetContainer(hit)
                hit.ref()
                req.connect('response', self._on_snippet_received, query, container, qstring, qmax)
                req.connect('closed', self._on_snippet_closed, query, container, qstring, qmax)
                self.beagle.send_request_async(req)
                continue
                            
            match = self._on_hit_added(query, hit, qstring, qmax)
            
            if match != None:
                hit_matches.append(match)                
            
        self._emit_query_ready(qstring, hit_matches)
        
    def show_config(self, parent):
        dialog = gtk.Dialog(_("Start Beagle Daemon?"), parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
    
        dialog.set_default_size (350, 150)
        dialog.add_button (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        dialog.add_button (_("Start Beagle Daemon"), gtk.RESPONSE_ACCEPT)
        label = gtk.Label (_("The Beagle daemon does not appear to be running.\n You need to start it to use the Beagle Live handler."))
        dialog.vbox.add (label)
        label.show()
    
        response = dialog.run()
        dialog.destroy()
        
        if response == gtk.RESPONSE_ACCEPT :
            logging.info("Starting Beagle Daemon.")
            if not spawn_async(["beagled"]):
                BeagleLiveHandler.INSTRUCTIONS = _("Failed to start beagled. Perhaps the beagle daemon isn't installed?")
                warn = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, 
                            type=gtk.MESSAGE_WARNING,
                            buttons=gtk.BUTTONS_CLOSE,
                            message_format=_("Failed to start Beagle"))
                warn.format_secondary_text (_("Perhaps the beagle daemon isn't installed?"))
                warn.run()
                warn.destroy()
        
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
                BeagleLiveHandler.INSTRUCTIONS = "Beagle daemon is not running."
                return False
            else:
                BeagleLiveHandler.INSTRUCTIONS = _("Beagled could not be found in your $PATH. Unable to start the beagled daemon")
                return False
        else:
            return True
