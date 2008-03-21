#!/usr/bin/env python
import gtk
import gtk.gdk
import sys
from os.path import abspath, join, dirname, exists
import logging
import gettext, locale
from gettext import gettext as _
import gnomeapplet
from optparse import OptionParser

# Return a standalone window that holds the applet
def build_window():
    app = gtk.Window(gtk.WINDOW_TOPLEVEL)
    # translators: This is the window title.
    app.set_title(_("Deskbar Applet"))
    app.connect("destroy", gtk.main_quit)
    
    applet = gnomeapplet.Applet()
    applet.set_flags(applet.flags() | gnomeapplet.EXPAND_MINOR)
    applet.get_orient = lambda: gnomeapplet.ORIENT_DOWN
    applet_factory(applet, None)
    applet.reparent(app)
        
    app.show_all()
    
    return app

def applet_factory(applet, iid):
    logging.info ('Starting Deskbar instance: %s %s', applet, iid)
    tray = DeskbarTray(applet)
    applet.add(tray)
    
    applet.show_all()
    return True

def check_deskbar_path ():
    root_dir = dirname(dirname(__file__))
    if exists(join(root_dir, "Makefile.am")):
    	# Running in uninstalled mode
    	sys.path.insert(0, abspath(root_dir))
    	logging.info ("Running uninstalled, adding %s to system path" % abspath(root_dir))

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')

# Delay loading of deskbar modules until we have the path set up,
# to allow running in uninstalled mode
check_deskbar_path()
import deskbar
import deskbar.defs
import deskbar.gtkexcepthook
from deskbar.ui.DeskbarTray import DeskbarTray

# Setup i18n
gettext.bindtextdomain('deskbar-applet', abspath(join(deskbar.defs.DATA_DIR, "locale")))
if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset('deskbar-applet','UTF-8')
gettext.textdomain('deskbar-applet')

locale.bindtextdomain('deskbar-applet', abspath(join(deskbar.defs.DATA_DIR, "locale")))
if hasattr(locale, 'bind_textdomain_codeset'):
    locale.bind_textdomain_codeset('deskbar-applet','UTF-8')
locale.textdomain('deskbar-applet')

try:
    # attempt to set a name for killall
    import deskbar.osutils
    deskbar.osutils.set_process_name ("deskbar-applet")
except:
    print "Unable to set processName"

# Enable threads
gtk.gdk.threads_init()

# Parse commandline options
usage = "deskbar-applet [OPTIONS]"
parser = OptionParser(usage=usage)
parser.add_option("-w", "--window", dest="window", action="store_true", help="Launch the applet in a standalone window for test purposes (default=no)")
parser.add_option("-v", "--version", dest="version", action="store_true", help="Print version")
parser.add_option("--oaf-activate-iid")
parser.add_option("--oaf-ior-fd")
(options, args) = parser.parse_args()

if options.version:
    print deskbar.defs.VERSION
    sys.exit()

if options.window:
    import gnome
    gnome.init(deskbar.defs.PACKAGE, deskbar.defs.VERSION)
    build_window()
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
else:
    gnomeapplet.bonobo_factory(
            "OAFIID:Deskbar_Applet_Factory",
            gnomeapplet.Applet.__gtype__,
            deskbar.defs.PACKAGE,
            deskbar.defs.VERSION,
            applet_factory)
