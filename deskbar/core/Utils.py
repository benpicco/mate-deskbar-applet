from deskbar.core.GconfStore import GconfStore
from deskbar.core._userdirs import *
from gettext import gettext as _
from htmlentitydefs import name2codepoint
from os.path import *
import deskbar
import deskbar.core.Categories
import deskbar.core.gnomedesktop
import gnome.ui
import gnomevfs
import gobject
import gtk
import gtk.gdk
import logging
import os, cgi, re

LOGGER = logging.getLogger(__name__)

PATH = [path for path in os.getenv("PATH").split(os.path.pathsep)
        if path.strip() != "" and exists(path) and isdir(path)]

ICON_THEME = gtk.icon_theme_get_default()
factory = gnome.ui.ThumbnailFactory(deskbar.ICON_HEIGHT)

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
        icon = deskbar.core.gnomedesktop.find_icon(ICON_THEME, icon, deskbar.ICON_HEIGHT, 0)
        if icon != None:
            return load_icon(icon)
        
# We load the icon file, and if it fails load an empty one
# If the iconfile is a path starting with /, load the file
# else try to load a stock or named icon name
def load_icon(icon, width=deskbar.ICON_HEIGHT, height=deskbar.ICON_HEIGHT):
    """
    If C{icon} starts with C{file://} a icon for the specific file is returnted.
    Otherwise, C{icon} should be the filename of an icon and it's returned as pixbuf.
    
    @return: gtk.gdk.Pixbuf
    """
    pixbuf = None
    if icon != None and icon != "":
        if icon.startswith("file://") and gnomevfs.exists(icon):
            icon, flags = gnome.ui.icon_lookup(ICON_THEME, factory,
                icon, "",
                gnome.ui.ICON_LOOKUP_FLAGS_SHOW_SMALL_IMAGES_AS_THEMSELVES)
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
                pixbuf = ICON_THEME.load_icon(splitext(icon)[0], width, gtk.ICON_LOOKUP_USE_BUILTIN)
        except Exception, msg1:
            try:
                pixbuf = ICON_THEME.load_icon(icon, width, gtk.ICON_LOOKUP_USE_BUILTIN)
            except Exception, msg2:
                LOGGER.error('load_icon:Icon Load Error:%s (or %s)' % (msg1, msg2))
                return ICON_THEME.load_icon("stock_unknown", width, gtk.ICON_LOOKUP_USE_BUILTIN)
                
    # an icon that is too tall will make the EntryCompletion look funny
    if pixbuf != None and pixbuf.get_height() > height:
        pixbuf = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
    return pixbuf

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
        gobject.spawn_async(args, flags=gobject.SPAWN_SEARCH_PATH)
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

def url_show_file(url, escape=True):
    """
    @param escape: Whether C{url} should be escaped or not 
    """
    try:
        if escape:
            url = gnomevfs.escape_host_and_path_string(url)
        gnomevfs.url_show(url)
        add_to_recent(url)
    except Exception, e:
        executed = False
        try:
            executed = spawn_async([gnomevfs.get_local_path_from_uri(url)])
        except:
            if not executed:
                if escape:
                    url = gnomevfs.escape_host_and_path_string(dirname(url))
                url_show(url)
                add_to_recent(url)

def url_show(url):
    try:
        gnomevfs.url_show(url)
    except Exception, e:
        message_dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE)
        message_dialog.set_markup("<span size='larger' weight='bold'>%s</span>\n\n '%s'" % (
            _("Cannot show URL:"), cgi.escape(url)))

        resp = message_dialog.run()
        if resp == gtk.RESPONSE_CLOSE:
            message_dialog.destroy()

def get_proxy():
    # TODO: Very dirty, should use CoreImpl class
    deskbarapplet = GconfStore.get_instance()
    if deskbarapplet.get_use_http_proxy():
        proxy_string = "http://%s:%d/" % (deskbarapplet.get_proxy_host(), deskbarapplet.get_proxy_port())
        proxies = {'http' : proxy_string}
        return proxies
    else:
        return None
