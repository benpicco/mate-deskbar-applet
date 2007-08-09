# -*- coding: utf-8 -*-
from gettext import gettext as _
from deskbar.defs import VERSION
import gtk, gtk.gdk, gnomevfs


def on_email(about, mail):
	gnomevfs.url_show("mailto:%s" % mail)

def on_url(about, link):
	gnomevfs.url_show(link)

gtk.about_dialog_set_email_hook(on_email)
gtk.about_dialog_set_url_hook(on_url)

def show_about(parent):
	about = gtk.AboutDialog()
	infos = {
		"name" : _("Deskbar"),
		"logo-icon-name" : "deskbar-applet",
		"version" : VERSION,
		"comments" : _("An all-in-one action bar."),
		"copyright" : "Copyright © 2004-2006\nNigel Tao, Raphael Slinckx, Mikkel Kamstrup Erlandsen, Sebastian Pölsterl.",
		"website" : "http://raphael.slinckx.net/deskbar",
		"website-label" : _("Deskbar Website"),
	}

	about.set_authors(["Nigel Tao <nigel.tao@myrealbox.com>",
					   "Raphael Slinckx <raphael@slinckx.net>",
					   "Mikkel Kamstrup Erlandsen <kamstrup@daimi.au.dk>",
					   "Sebastian Pölsterl <marduk@k-d-w.org>"])
#	about.set_artists([])
#	about.set_documenters([])
	
	#translators: These appear in the About dialog, usual format applies.
	about.set_translator_credits( _("translator-credits") )
	
	for prop, val in infos.items():
		about.set_property(prop, val)
	
	about.connect("response", lambda self, *args: self.destroy())
	about.set_screen(parent.get_screen())
	about.show_all()
