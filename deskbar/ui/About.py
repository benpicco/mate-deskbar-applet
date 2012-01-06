# -*- coding: utf-8 -*-
from deskbar.core.Utils import launch_default_for_uri
from deskbar.defs import VERSION
from gettext import gettext as _
import gtk
import gtk.gdk


def on_email(about, mail):
    launch_default_for_uri("mailto:%s" % mail)

def on_url(about, link):
    launch_default_for_uri(link)

gtk.about_dialog_set_email_hook(on_email)
gtk.about_dialog_set_url_hook(on_url)

def show_about(parent):
    about = gtk.AboutDialog()
    infos = {
        "authors": ["Nigel Tao <nigel.tao@myrealbox.com>",
                    "Raphael Slinckx <raphael@slinckx.net>",
                    "Mikkel Kamstrup Erlandsen <kamstrup@daimi.au.dk>",
                    "Sebastian Pölsterl <sebp@k-d-w.org>"],
        "comments" : _("An all-in-one action bar."),
        "copyright" : "Copyright © 2004-2008\nNigel Tao, Raphael Slinckx, Mikkel Kamstrup Erlandsen, Sebastian Pölsterl.",
        "documenters" : ["Phil Bull <philbull@gmail.com>", "Qing Gan"],
        "logo-icon-name" : "deskbar-applet",
        "name" : _("Deskbar"),
        "version" : VERSION,
        "website" : "http://projects.gnome.org/deskbar-applet/",
        "website-label" : _("Deskbar Website"),   
    }
    
    #translators: These appear in the About dialog, usual format applies.
    about.set_translator_credits( _("translator-credits") )
    
    for prop, val in infos.items():
        about.set_property(prop, val)
    
    about.connect("response", lambda self, *args: self.destroy())
    about.set_screen(parent.get_screen())
    about.show_all()
