from gettext import gettext as _
import re
import deskbar.interfaces.Module
import deskbar.interfaces.Match
from deskbar.defs import VERSION
from deskbar.handlers.actions.OpenWithNautilusAction import OpenWithNautilusAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from deskbar.handlers.actions.SendEmailToAction import SendEmailToAction

HANDLERS = ["WebAddressHandler"]

AUTH_REGEX = re.compile(r'[a-zA-Z]+://\w+(:\w+)?@([\w\-]+\.)+[\w\-]+(:\d+)?(/.*)?')
HTTP_REGEX = re.compile(r'^(?P<method>[a-zA-Z]+://)?([\w\-]+\.)+[\w\-]+(:\d+)?(/.*)?$')
MAIL_REGEX = re.compile(r'^([\w\-]+\.)*[\w\-]+@([\w\-]+\.)*[\w\-]+$')

class WebAddressMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, url=None, has_method=True, **args):
        deskbar.interfaces.Match.__init__(self, name=name, icon="stock_internet", category="web", **args)
        self.url = url
        
        if not has_method and not self.url.startswith("http://"):
            self.url = "http://" + url
            
        if self.url.startswith("http"):
            self.add_action( ShowUrlAction(name, self.url) )
        else:
            self.add_action( OpenWithNautilusAction(name, self.url) )
    
    def get_hash(self):
        return self.url

class EmailAddressMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, mail=None, **args):
        deskbar.interfaces.Match.__init__(self, name=name, icon="stock_mail", category="people", **args)
        self.mail = mail
        self.add_action( SendEmailToAction(name, mail) )
    
    def get_hash(self):
        return self.mail
        
class WebAddressHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("stock_internet"),
             "name": _("Web"),
             "description": _("Open web pages and send emails by typing a complete address"),
             "version": VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
    
    def query(self, query):
        result = self.query_http(query)
        result += self.query_mail(query)
        self._emit_query_ready(query, result )
        
    def query_http(self, query):
        match = AUTH_REGEX.match(query)
        if match != None:
            return [WebAddressMatch(query, query)]
        
        match = HTTP_REGEX.match(query)
        if match != None:
            return [WebAddressMatch(query, query, (match.group('method') != None), priority=self.get_priority())]
    
        return []
        
    def query_mail(self, query):
        if MAIL_REGEX.match(query) != None:
            return [EmailAddressMatch(query, query, priority=self.get_priority())]
        else:
            return []
