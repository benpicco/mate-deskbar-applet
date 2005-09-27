from os.path import join
from gettext import gettext as _
from deskbar.defs import VERSION
import gtk, gtk.gdk, gnomevfs, gobject
import deskbar


def on_email(about, mail):
	gnomevfs.url_show("mailto:%s" % mail)

def on_url(about, link):
	gnomevfs.url_show(link)

gtk.about_dialog_set_email_hook(on_email)
gtk.about_dialog_set_url_hook(on_url)

deskbar_logo = None
try:
	deskbar_logo = gtk.gdk.pixbuf_new_from_file(join(deskbar.ART_DATA_DIR, "deskbar-applet.png"))
except gobject.GError, msg:
	print 'Error:about:', msg

def show_about():
	about = gtk.AboutDialog()
	infos = {
		"name" : _("Deskbar Applet"),
		"logo" : deskbar_logo,
		"version" : VERSION,
		"comments" : _("An all-in-one search bar."),
		"copyright" : "Copyright (c) 2004-2005 Nigel Tao.",
		"website" : "http://browserbookapp.sourceforge.net/deskbar.html",
		"website-label" : _("Deskbar Applet Website"),
	}

	about.set_authors(["Nigel Tao <nigel.tao@myrealbox.com>", "Raphaël Slinckx <raphael@slinckx.net>"])
#	about.set_artists([])
#	about.set_documenters([])
#	about.set_translator-credits([])
	
	for prop, val in infos.items():
		about.set_property(prop, val)
	
	about.show_all()
