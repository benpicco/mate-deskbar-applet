from deskbar.defs import VERSION
from deskbar.core.Utils import get_proxy
from gettext import gettext as _
import base64
import deskbar
import gtk
import gobject
import logging
import threading
import re
import urllib
import gnomekeyring

LOGGER = logging.getLogger(__name__)

class Account :
    """
    This is an abstraction used to make it easier to move
    away from a GConf password storage solution (Seahorse anyone?)
    
    WARNING: This API is synchronous. This does not matter much to deskbar since
             web based modules will likely run in threads anyway.
    
    This class is based on work found in Sebastian Rittau's blog
    found on http://www.rittau.org/blog/20070726-00. Copied with permission.
    """
    def __init__(self, host, realm):
        self._realm = realm
        self._host = host
        self._protocol = "http"
        self._keyring = gnomekeyring.get_default_keyring_sync()

    def has_credentials(self):
        """
        @returns: True if and only if the credentials for this account is known
        """
        try:
            attrs = {"server": self._host, "protocol": self._protocol}
            items = gnomekeyring.find_items_sync(gnomekeyring.ITEM_NETWORK_PASSWORD, attrs)
            if len(items) > 0 :
                if items[0].attributes["user"] != "" and \
                   items[0].secret != "" :
                   return True
                else :
                    return False
        except gnomekeyring.DeniedError:
            return False
        except gnomekeyring.NoMatchError:
            return False
    
    def get_host (self):
        return self._host
    
    def get_realm (self):
        return self._realm
    
    def get_credentials(self):
        """
        @return: A tuple C{(user, password)} or throws an exception if the
            credentials for the account are not known
        """
        attrs = {"server": self._host, "protocol": self._protocol}
        items = gnomekeyring.find_items_sync(gnomekeyring.ITEM_NETWORK_PASSWORD, attrs)
        
        if (len(items) > 1):
            LOGGER.warn ("More than one account found for %s" % self._host)
        
        return (items[0].attributes["user"], items[0].secret)

    def set_credentials(self, user, pw):
        """
        Store or update username and password for account
        """
        # Note: attrs is used to look up the account for old user credentials
        attrs = {
                "server": self._host,
                "protocol": self._protocol,
            }
        
        LOGGER.debug ("Updating credentials for %s" % self._host)
        
        keyring = gnomekeyring.get_default_keyring_sync()
        
        # Look up all accounts registered for this service and realm and delete
        # them. We get weird errors if more than one account is present
        try:
            items = gnomekeyring.find_items_sync (gnomekeyring.ITEM_NETWORK_PASSWORD,
                                              attrs)
        except gnomekeyring.NoMatchError:
            LOGGER.debug ("No existing accounts for %s" % self._host)
            items = []
            
        for item in items:
            LOGGER.debug ("Purging account %s@%s" % 
                          (item.attributes["user"], item.attributes["server"]))
            gnomekeyring.item_delete_sync (keyring, item.item_id)
        
        # Add the 'user' attribute to attrs and commit it to the keyring
        LOGGER.debug ("Creating new account %s@%s" % (user, self._host))
        attrs["user"] = user
        gnomekeyring.item_create_sync(keyring,
                                      gnomekeyring.ITEM_NETWORK_PASSWORD,
                                      self._realm, attrs, pw, True)
        
        LOGGER.debug ("Credential update success")

class AccountDialog (gtk.MessageDialog):
    """
    A simple dialog for managing an L{Account}. It must be used like any other
    gtk dialog, like:
    
        dialog.show_all()
        dialog.run()            
        dialog.destroy()
    
    """
    def __init__ (self,
                  account,
                  dialog_parent=None,
                  dialog_type=gtk.MESSAGE_QUESTION,
                  dialog_flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT):
        """
        @param account: L{Account} to manage
        """
        gtk.MessageDialog.__init__(self,
                                   parent=dialog_parent,
                                   type=dialog_type,
                                   flags=dialog_flags,
                                   buttons=gtk.BUTTONS_OK_CANCEL)
        
        self._account = account
        self._response = None
        
        self.connect ("response", self._on_response)
        self.set_markup (_("<big><b>Login for %s</b></big>") % account.get_host())
        self.format_secondary_markup (_("Please provide your credentials for <b>%s</b>") % account.get_host())
        self.set_title (_("Credentials for %s") % account.get_host())
        
        self._user_entry = gtk.Entry()
        self._password_entry = gtk.Entry()
        self._password_entry.set_property("visibility", False) # Show '*' instead of text
        
        user_label = gtk.Label (_("User name:"))
        password_label = gtk.Label (_("Password:"))
        
        table = gtk.Table (2, 2)
        table.set_row_spacings(3)
        table.set_col_spacings(6)
        table.attach (user_label, 0, 1, 0, 1)
        table.attach (self._user_entry, 1, 2, 0, 1)
        table.attach (password_label, 0, 1, 1, 2)
        table.attach (self._password_entry, 1, 2, 1, 2)
        
        self.vbox.pack_end (table)
        
        if self._account.has_credentials():
            user, password = self._account.get_credentials()
            self._user_entry.set_text(user)
            self._password_entry.set_text(password)
        
        self._set_ok_sensitivity ()
        self._user_entry.connect ("changed", lambda entry : self._set_ok_sensitivity())
        self._password_entry.connect ("changed", lambda entry : self._set_ok_sensitivity())
            
    def _on_response (self, dialog, response_id):
        self._response = response_id
        if response_id == gtk.RESPONSE_OK:
            LOGGER.debug ("Registering credentials for %s on %s" % (self._account.get_realm(), self._account.get_host()))
            self._account.set_credentials(self.get_user(),
                                          self.get_password())
        else:
            LOGGER.debug ("Credential registration for %s cancelled" % self._account.get_host())
    
    def _set_ok_sensitivity (self):
        if self._user_entry.get_text() != "" and self._password_entry.get_text() != "":
            self.set_response_sensitive(gtk.RESPONSE_OK, True)
        else:
            self.set_response_sensitive(gtk.RESPONSE_OK, False)
    
    def get_user (self):
        return self._user_entry.get_text()
    
    def get_password (self):
        return self._password_entry.get_text()
    
    def get_response (self):
        """
        @return: C{gtk.RESPONSE_OK} if the user pressed OK or 
            C{gtk.RESPONSE_CANCEL} on cancellation. C{None} if no response
            has been recorded yet
        """
        return self._response
        
class ConcurrentRequestsException (Exception):
    """
    Raised by L{GnomeURLopener} if there are multiple concurrent
    requests to L{GnomeURLopener.open_async}.
    """
    def __init__ (self):
        Exception.__init__ (self)

class AuthenticationAborted (Exception):
    """
    Raised by L{GnomeURLopener} if the user cancels a request for
    providing credentials
    """
    def __init__ (self):
        Exception.__init__ (self)


class GnomeURLopener (urllib.FancyURLopener):
    """
    A subclass of C{urllib.URLopener} able to intercept user/password requests
    and pass them through an L{Account}, displaying a L{AccountDialog} if
    necessary.
    
    Note on proxies: The GnomeURLopener will not react to any subsequent changes
                     to the Gnome proxy settings. Therefore preferably create
                     a new fresh GnomeURLopener each time you need one
    """
    
    def __init__ (self, account, extra_widget_factory=None):
        """
        @param account: The L{Account} object to request credentials from
        @param extra_widget_factory: This optional parameter may point to a
                                     C{callable} returning a C{gtk.Widget} which
                                     will be packed into the L{AccountDialog}
                                     when it is spawned. The callable may also
                                     return C{None} if no widgets should be
                                     added.
        """
        proxies = get_proxy()
        urllib.FancyURLopener.__init__ (self, proxies)
        
        self._account = account
        self._thread = None
        self._authentication_retries = 0
        self._success = True
        self._extra_widget_factory = extra_widget_factory
        
        LOGGER.debug ("Using proxies: %s" % proxies)
        
    def prompt_user_passwd (self, host, realm):
        """
        Override of the same method in C{urllib.FancyURLopener} to display
        and L{AccountDialog} on user/pass requests.
        """
        LOGGER.debug ("Requesting credentials for host: '%s', realm '%s'" % (host, realm))
        
        self._authentication_retries = self._authentication_retries + 1
        
        gtk.gdk.threads_enter ()
        
        # If these credentials have failed before, prompt the user
        if self._authentication_retries > 1:
            LOGGER.debug ("Invalid credentials for %s in keyring. Asking for them again..." %
                          self._account.get_host())
            login_dialog = AccountDialog(self._account,
                                         dialog_type=gtk.MESSAGE_WARNING)
            login_dialog.set_markup (_("<big><b>Login to %s rejected</b></big>") % self._account.get_host())
            login_dialog.format_secondary_markup (_("Please verify your credentials for <b>%s</b>") % self._account.get_host())
            
            self._install_extra_widget (login_dialog)
            
            login_dialog.show_all()
            login_dialog.run()            
            login_dialog.destroy()
            self._authentication_retries = 0
            if login_dialog.get_response() == gtk.RESPONSE_CANCEL:
                LOGGER.debug ("Login to %s aborted" % self._account.get_host())
                gtk.gdk.threads_leave ()
                raise AuthenticationAborted()
        
        # Make sure we do have the credentials
        if not self._account.has_credentials ():
            LOGGER.debug ("No credentials for %s in keyring. Asking for them..." %
                          self._account.get_host())
            login_dialog = AccountDialog(self._account)
            
            self._install_extra_widget (login_dialog)
            
            login_dialog.show_all()
            login_dialog.run()            
            login_dialog.destroy()
            if login_dialog.get_response() == gtk.RESPONSE_CANCEL:
                LOGGER.debug ("Login to %s aborted" % self._account.get_host())
                gtk.gdk.threads_leave ()
                raise AuthenticationAborted()
        
        creds = self._account.get_credentials()
        
        gtk.gdk.threads_leave ()
        
        return creds
    
    def _install_extra_widget (self, login_dialog):
        """
        Install the extra widget returned by the extra_widget_factory into
        login_dialog, if applicable
        """
        if callable(self._extra_widget_factory):
                widget = self._extra_widget_factory()
                if widget != None:
                    if isinstance (widget, gtk.Widget):
                        login_dialog.vbox.pack_start (widget)
                    else:
                        # The factory returned a non-None non-widget object
                        LOGGER.error ("%s returned a non-gtk.Widget instance: %s" % (self._extra_widget_factory, type(widget)))
    
    def open_async (self, url, payload=None, callback=None):
        """
        Open a URL asynchronously. When the request has been completed the
        C{"done"} signal of this class is emitted.
        
        If C{payload} is not C{None} the http request
        will be a C{POST} with the given payload. The way to construct the
        post payload is typically by calling C{urllib.urlencode} on a key-value
        C{dict}. For example:
        
            urllib.urlencode({"status" : msg})
        
        This method will raise a L{ConcurrentRequestsException} if there is
        already a pending open request when a new one is issued.
        
        @param url: The URL to open asynchronously
        @param payload: Optional payload in case of a POST request. See above
        """
        LOGGER.debug ("Async open on: %s with payload %s" % (url,payload))
        if self._thread :
            raise ConcurrentRequestsException()
    
        if payload != None :
            async_args = ((url, payload), callback)
        else :
            async_args = ((url, ), callback)
        
        self._thread = threading.Thread (target=self._do_open_async,
                                         args=async_args,
                                         name="GnomeURLopener")
        
        self._thread.start()
    
    def get_success (self):
        """
        @return: C{True} if and only if no error has occured
        """
        return self._success
        
    def _do_open_async (self, *args):
        self._authentication_retries = 0
        self._thread = None
        
        info = None
        open_args, callback = args
        
        try:
            info = self.open (*open_args)
        except AuthenticationAborted:
            LOGGER.debug ("Detected authentication abort")
            self._success = True # The user should not be warned
        except IOError, e:
            LOGGER.warn ("Caught IOError when posting: %s" % e)
            self._success = False            
            
        gtk.gdk.threads_enter()
        if callback != None and callable(callback):
            callback(self, info)
        gtk.gdk.threads_leave()

