#!/usr/bin/env python
#
# (C) 2005 Nigel Tao.
# Licensed under the GNU GPL.


import gnomeapplet
import gtk
import sys
import deskbar.applet


def applet_factory(applet, iid):
	deskbar.applet.DeskbarApplet(applet)
	return True


if __name__ == "__main__":
	if (len(sys.argv) == 2) and (sys.argv[1] == "-print"):
		print "No problems so far."

	elif (len(sys.argv) == 2) and (sys.argv[1] == "-window"):
		main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		main_window.set_title("Deskbar Applet")
		main_window.connect("destroy", gtk.main_quit)
		
		applet = gnomeapplet.Applet()
		applet_factory(applet, None)
		applet.reparent(main_window)
		
		main_window.show_all()
		gtk.main()

	else:
		gnomeapplet.bonobo_factory( \
			"OAFIID:Deskbar_Applet_Factory", \
			gnomeapplet.Applet.__gtype__, \
			"deskbar-applet", \
			"0", \
			applet_factory)
