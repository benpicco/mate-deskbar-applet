import gtk, gnomevfs
from gettext import gettext as _
import deskbar
from deskbar.defs import VERSION

def on_email(about, mail):
	gnomevfs.url_show("mailto:%s" % mail)

def on_url(about, link):
	gnomevfs.url_show(link)

gtk.about_dialog_set_email_hook(on_email)
gtk.about_dialog_set_url_hook(on_url)

def show_about():
	about = gtk.AboutDialog()
	infos = {
		"name" : _("Deskbar Applet"),
		"logo" : deskbar.DESKBAR_BIG_IMAGE.get_pixbuf(),
		"version" : VERSION,
		"comments" : _("An all-in-one search bar."),
		"copyright" : "Copyright (c) 2004-2005 Nigel Tao.",
		"website" : "http://browserbookapp.sourceforge.net/deskbar.html",
		"website-label" : _("Deskbar Applet Website"),
	}

	about.set_authors(["Nigel Tao <nigel.tao@myrealbox.com>"])
#	about.set_artists([])
#	about.set_documenters([])
#	about.set_translator-credits([])
	
	for prop, val in infos.items():
		about.set_property(prop, val)
	
	about.show_all()
