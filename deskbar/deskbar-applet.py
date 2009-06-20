#!/usr/bin/env python
import gtk
import gtk.gdk
import sys
from os.path import abspath, join, dirname, exists
import logging
import gettext
import locale
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
    applet.get_orient = lambda: gnomeapplet.ORIENT_DOWN
    applet_factory(applet, None)
    applet.reparent(app)
        
    app.show_all()
    
    return app

def applet_factory(applet, iid):
    logging.info ('Starting Deskbar instance: %s %s', applet, iid)
    
    app = DeskbarApplet(applet)
    app.show_all()
    
    return True

def check_deskbar_path ():
    root_dir = dirname(dirname(__file__))
    if exists(join(root_dir, "Makefile.am")):
    	# Running in uninstalled mode
    	sys.path.insert(0, abspath(root_dir))
    	logging.info ("Running uninstalled, adding %s to system path" % abspath(root_dir))

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M:%S')

# Delay loading of deskbar modules until we have the path set up,
# to allow running in uninstalled mode
check_deskbar_path()
import deskbar
import deskbar.defs
import deskbar.gtkexcepthook

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
parser.add_option("-t", "--tray", dest="tray", action="store_true", help="Run Deskbar as a tray icon instead of an applet")
parser.add_option("-v", "--version", dest="version", action="store_true", help="Print version")
parser.add_option("-d", "--debug", dest="debug", action="store_true", help="Turn debug messages on")
parser.add_option("--oaf-activate-iid")
parser.add_option("--oaf-ior-fd")
(options, args) = parser.parse_args()

if options.version:
    print deskbar.defs.VERSION
    sys.exit()

if options.debug:
    logging.getLogger().setLevel(logging.DEBUG)

if options.tray:
    from deskbar.ui.DeskbarStatusIcon import DeskbarStatusIcon
    
    deskbar_status_icon = DeskbarStatusIcon ()
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
elif options.window:
    from deskbar.ui.DeskbarApplet import DeskbarApplet

    build_window()
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
else:
    from deskbar.ui.DeskbarApplet import DeskbarApplet
    
    gnomeapplet.bonobo_factory(
            "OAFIID:Deskbar_Applet_Factory",
            DeskbarApplet.__gtype__,
            deskbar.defs.PACKAGE,
            deskbar.defs.VERSION,
            applet_factory)
