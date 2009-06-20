from deskbar.core.GconfStore import GconfStore
from deskbar.core._userdirs import *
from gettext import gettext as _
from htmlentitydefs import name2codepoint
from os.path import *
import cgi
import deskbar
import gnomedesktop
import gio
import glib
import gtk
import gtk.gdk
import locale
import logging
import os
import re
import base64

LOGGER = logging.getLogger(__name__)

PATH = [path for path in os.getenv("PATH").split(os.path.pathsep)
        if path.strip() != "" and exists(path) and isdir(path)]

ICON_THEME = gtk.icon_theme_get_default()

# This pattern matches a character entity reference (a decimal numeric
# references, a hexadecimal numeric reference, or a named reference).
charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')

def htmldecode(text):
    """Decode HTML entities in the given text."""
    if type(text) is unicode:
        uchr = unichr
    else:
        uchr = lambda value: value > 255 and unichr(value) or chr(value)
    
    def entitydecode(match, uchr=uchr):
        entity = match.group(1)
        if entity.startswith('#x'):
            return uchr(int(entity[2:], 16))
        elif entity.startswith('#'):
            return uchr(int(entity[1:]))
        elif entity in name2codepoint:
            return uchr(name2codepoint[entity])
        else:
            return match.group(0)
    
    return charrefpat.sub(entitydecode, text)

def strip_html(string):
    return re.sub(r"<.*?>|</.*?>","",string)
    
def more_information_dialog(parent, title, content):
    """
    Display a information dialog
    
    @param parent: Parent window 
    @param title: Title of the dialog
    @param conent: Conent of the dialog 
    """
    message_dialog = gtk.MessageDialog(parent=parent, buttons=gtk.BUTTONS_CLOSE)
    message_dialog.set_markup("<span size='larger' weight='bold'>%s</span>\n\n%s" % (cgi.escape(title), cgi.escape(content)))
    resp = message_dialog.run()
    if resp == gtk.RESPONSE_CLOSE:
        message_dialog.destroy()
        
def get_xdg_data_dirs():
    dirs = os.getenv("XDG_DATA_HOME")
    if dirs == None:
        dirs = expanduser("~/.local/share")
    
    sysdirs = os.getenv("XDG_DATA_DIRS")
    if sysdirs == None:
        sysdirs = "/usr/local/share:/usr/share"
    
    dirs = "%s:%s" % (dirs, sysdirs)
    return [dir for dir in dirs.split(":") if dir.strip() != "" and exists(dir)]

def load_icon_for_desktop_icon(icon):
    if icon != None:
        icon = gnomedesktop.find_icon(ICON_THEME, icon, deskbar.ICON_HEIGHT, 0)
        if icon != None:
            return load_icon(icon)
        
# We load the icon file, and if it fails load an empty one
# If the iconfile is a path starting with /, load the file
# else try to load a stock or named icon name
def load_icon(icon, width=deskbar.ICON_HEIGHT, height=deskbar.ICON_HEIGHT):
    """
    If C{icon} starts with C{file://} a icon for the specific file is returned.
    Otherwise, C{icon} should be the filename of an icon and it's returned as pixbuf.
    
    @return: gtk.gdk.Pixbuf
    """
    pixbuf = None
    if icon != None and icon != "":
        if icon.startswith("file://"):
            gfile = gio.File(uri=icon)
            if gfile.query_exists():
                info = gfile.query_info("thumbnail::path", 0)
                icon = info.get_attribute_byte_string("thumbnail::path")
        try:
            our_icon = join(deskbar.ART_DATA_DIR, icon)
            custom_icon = join(deskbar.USER_HANDLERS_DIR[0], icon)
            if exists(our_icon):
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(our_icon, width, height)
            elif exists( custom_icon ):
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(custom_icon, width, height)
            elif icon.startswith("/"):
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon, width, height)
            else:
                pixbuf = load_icon_from_icon_theme(splitext(icon)[0], width)
        except Exception, msg1:
            try:
                pixbuf = load_icon_from_icon_theme(icon, width)
            except Exception, msg2:
                LOGGER.warning ("Icon %s Load Error: %s (or %s)", icon, msg1, msg2)
                pixbuf = _get_fall_back_icon()
                
    # an icon that is too tall will make the EntryCompletion look funny
    if pixbuf != None and pixbuf.get_height() > height:
        pixbuf = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
    return pixbuf

def load_icon_from_icon_theme(iconname, size):
    return ICON_THEME.load_icon(iconname, size, gtk.ICON_LOOKUP_USE_BUILTIN)

def load_base64_icon (base64_str):
    """
    Load a base64 encoded image as a C{gtk.gdk.Pixbuf}.
    
    @param base64_str: a C{string} with a base64 encoded image
    @return: A C{gtk.gdk.Pixbuf} or a fallback icon in case there are errors
        parsing C{base64_str}.
    """
    loader = gtk.gdk.PixbufLoader()
    
    try:
        try:
            loader.set_size(deskbar.ICON_HEIGHT, deskbar.ICON_HEIGHT)
            loader.write(base64.b64decode(base64_str))
        except Exception, e:
            LOGGER.warning ("Failed to read base64 encoded image: %s" % e)
        except gobject.GError, ee:
            LOGGER.warning ("Failed to read base64 encoded image: %s" % ee)
    finally:
        loader.close()
        
    pixbuf = loader.get_pixbuf()
    if pixbuf :
        return pixbuf
    
    return _get_fall_back_icon()

def _get_fall_back_icon():
    """
    @return: stock_unknown icon or C{None}
    """
    try:
        return load_icon_from_icon_theme("stock_unknown", width)
    except Exception, msg:
        LOGGER.warning ("Icon `stock_unknown' is not present in theme")
        return None

def is_program_in_path(program):
    """
    Whether C{program} is in PATH
    """
    for path in PATH:
        prog_path = join(path, program)
        if exists(prog_path) and isfile(prog_path) and is_executable(prog_path):
            return True
        
def is_executable(prog_path):
    return os.access(prog_path, os.F_OK | os.R_OK | os.X_OK)

def spawn_async(args):
    try:
        glib.spawn_async(args, flags=glib.SPAWN_SEARCH_PATH)
        return True
    except Exception, e:
        message_dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE)
        message_dialog.set_markup("<span size='larger' weight='bold'>%s</span>\n\n '%s'" % (
            _("Cannot execute program:"), cgi.escape(' '.join(args))))

        resp = message_dialog.run()
        if resp == gtk.RESPONSE_CLOSE:
            message_dialog.destroy()

        return False

def add_to_recent(uri):
    if hasattr(gtk, "recent_manager_get_default"):
        # add the file to the list of recently opened files
        manager = gtk.recent_manager_get_default()
        manager.add_item(uri)

def launch_default_for_uri(uri_string):
    """
    Open uri_string with the default application
    according to content type
    
    @type uri_string: str 
    """
    gfile = gio.File(uri=uri_string)
    appinfo = gfile.query_default_handler()
    
    if appinfo != None:
        appinfo.launch([gfile], None)
    else:
        LOGGER.error("Could not detect default application for %s", gfile.get_uri())

def launch_default_for_uri_and_scheme(uri_string):
    """
    Open uri_string with the default application
    according to scheme
    
    @type uri_string: str 
    """
    gfile = gio.File(uri=uri_string)
    appinfo = gfile.query_default_handler(None)
    
    if appinfo != None:
        appinfo.launch_uris([uri_string], None)
    else:
        LOGGER.error("Could not detect default application for %s", gfile.get_uri())
        
def uri_has_default_handler(uri_string):
    """
    Returns True if there's a default application
    to open the specified URI
    @type uri_string: str 
    """
    gfile = gio.File(uri=uri_string)
    try:
        appinfo = gfile.query_default_handler(None)
    except Exception, e:
        LOGGER.error("Error retrieving default application for %s: %s",
                     gfile.get_uri(), str(e))
        return False
    
    return (appinfo != None)
    
def url_show_file(url, escape=True):
    """
    @param escape: Whether C{url} should be escaped or not 
    """
    try:
        if escape:
            url = gio.File(uri=url).get_uri()
        launch_default_for_uri(url)
        add_to_recent(url)
    except Exception, e:
        executed = False
        try:
            executed = spawn_async([gio.File(uri=url).get_path()])
        except:
            if not executed:
                if escape:
                    url = gio.File(uri=url).get_uri()
                url_show(url)
                add_to_recent(url)

def url_show(url):
    try:
        launch_default_for_uri(url)
    except Exception, e:
        LOGGER.exception(e)
        message_dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE)
        message_dialog.set_markup("<span size='larger' weight='bold'>%s</span>\n\n '%s'" % (
            _("Cannot show URL:"), cgi.escape(url)))

        resp = message_dialog.run()
        if resp == gtk.RESPONSE_CLOSE:
            message_dialog.destroy()

# Make gtk.LinkButtons call url_show()
gtk.link_button_set_uri_hook (lambda button, url : url_show(url))

def get_proxy():
    # TODO: Very dirty, should use CoreImpl class
    deskbarapplet = GconfStore.get_instance()
    if deskbarapplet.get_use_http_proxy():
        proxy_string = "http://%s:%d/" % (deskbarapplet.get_proxy_host(), deskbarapplet.get_proxy_port())
        proxies = {'http' : proxy_string}
        return proxies
    else:
        return None
    
def get_locale_lang():
    """
    @returns language code corresponding to RFC 1766 of currently used locale
    or None when the code is unknown
    """
    try:
        localelang = locale.getlocale()[0]
    except ValueError:
        return None
    
    return localelang
