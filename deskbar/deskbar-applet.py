#!/usr/bin/env python
#
# (C) 2005 Nigel Tao.
# Licensed under the GNU GPL.
PROFILE = False
if PROFILE:
	import statprof
	statprof.start()

import gobject
gobject.threads_init()

import gtk, gnomeapplet
import getopt, sys
from os.path import *

# Allow to use uninstalled
def _check(path):
	return exists(path) and isdir(path) and isfile(path+"/AUTHORS")

name = join(dirname(__file__), '..')
if _check(name):
	print 'Running uninstalled deskbar, modifying PYTHONPATH'
	sys.path.insert(0, abspath(name))
else:
	sys.path.insert(0, abspath("@PYTHONDIR@"))
	print "Running installed deskbar, using [@PYTHONDIR@:$PYTHONPATH]"

# Now the path is set, import our applet
import deskbar, deskbar.DeskbarApplet, deskbar.defs

try:
	# attempt to set a name for killall
	import deskbar.osutils
	deskbar.osutils.set_process_name ("deskbar-applet")
except:
	print "Unable to set processName"

import gettext, locale
gettext.bindtextdomain('deskbar-applet', abspath(join(deskbar.defs.DATA_DIR, "locale")))
if hasattr(gettext, 'bind_textdomain_codeset'):
	gettext.bind_textdomain_codeset('deskbar-applet','UTF-8')
gettext.textdomain('deskbar-applet')

locale.bindtextdomain('deskbar-applet', abspath(join(deskbar.defs.DATA_DIR, "locale")))
if hasattr(locale, 'bind_textdomain_codeset'):
	locale.bind_textdomain_codeset('deskbar-applet','UTF-8')
locale.textdomain('deskbar-applet')

import gtkexcepthook

def applet_factory(applet, iid):
	print 'Starting Deskbar instance:', applet, iid
	deskbar.DeskbarApplet.DeskbarApplet(applet)
	return True

# Return a standalone window that holds the applet
def build_window():
	app = gtk.Window(gtk.WINDOW_TOPLEVEL)
	app.set_title("Deskbar Applet")
	app.connect("destroy", gtk.main_quit)
	app.set_property('resizable', False)
	
	applet = gnomeapplet.Applet()
	applet.get_orient = lambda: gnomeapplet.ORIENT_DOWN
	applet_factory(applet, None)
	applet.reparent(app)
		
	app.show_all()
	
	return app
		
		
def usage():
	print """=== Deskbar applet: Usage
$ deskbar-applet [OPTIONS]

OPTIONS:
	-h, --help			Print this help notice.
	-w, --window		Launch the applet in a standalone window for test purposes (default=no).
	-c, --cuemiac		Launch the Cuemiac UI (when in window mode) (default=no).
	"""
	sys.exit()
	
if __name__ == "__main__":	
	standalone = False
	cuemiac = False
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hwc", ["help", "window", "cuemiac"])
	except getopt.GetoptError:
		# Unknown args were passed, we fallback to bahave as if
		# no options were passed
		opts = []
		args = sys.argv[1:]
	
	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
		elif o in ("-w", "--window"):
			standalone = True
		elif o in ("-c", "--cuemiac"):
			cuemiac = True
	
	if standalone:
		if cuemiac:
			deskbar.UI_OVERRIDE = deskbar.CUEMIAC_UI_NAME
		else:
			deskbar.UI_OVERRIDE = deskbar.ENTRIAC_UI_NAME

		import gnome
		gnome.init(deskbar.defs.PACKAGE, deskbar.defs.VERSION)
		build_window()
		gtk.main()
	else:
		gnomeapplet.bonobo_factory(
			"OAFIID:Deskbar_Applet_Factory",
			gnomeapplet.Applet.__gtype__,
			deskbar.defs.PACKAGE,
			deskbar.defs.VERSION,
			applet_factory)
	
	if PROFILE:
		statprof.stop()
		statprof.display()

