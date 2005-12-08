from os.path import join
from gettext import gettext as _
from deskbar.defs import VERSION
from deskbar.handler_utils import load_icon
import gtk, gtk.gdk, gnomevfs, gobject
import deskbar


def on_email(about, mail):
	gnomevfs.url_show("mailto:%s" % mail)

def on_url(about, link):
	gnomevfs.url_show(link)

gtk.about_dialog_set_email_hook(on_email)
gtk.about_dialog_set_url_hook(on_url)

deskbar_logo = load_icon("deskbar-applet.svg", 96, 96)
def show_about():
	about = gtk.AboutDialog()
	infos = {
		"name" : _("Deskbar"),
		"logo" : deskbar_logo,
		"version" : VERSION,
		"comments" : _("An all-in-one action bar."),
		"copyright" : "Copyright (c) 2004-2005 Nigel Tao, Raphael Slinckx, Mikkel Kamstrup Erlandsen.",
		"website" : "http://raphael.slinckx.net/deskbar",
		"website-label" : _("Deskbar Website"),
	}

	about.set_authors(["Nigel Tao <nigel.tao@myrealbox.com>", "Raphael Slinckx <raphael@slinckx.net>", "Mikkel Kamstrup Erlandsen <kamstrup@daimi.au.dk>"])
#	about.set_artists([])
#	about.set_documenters([])
	
	#translators: Please keep it like "name <email@dot.com>". One line per translator.
	translator_credits = _("translator-credits")
	if translator_credits != "translator-credits":
		about.set_translator_credits([name for name in translator_credits.split('\n') if name != ""])
	
	for prop, val in infos.items():
		about.set_property(prop, val)
	
	about.show_all()
