import gtk
import deskbar


def show_about():
	about = gtk.AboutDialog()
	about.set_name("Deskbar")
	about.set_version(deskbar.VERSION)
	about.set_comments("An all-in-one search bar.")
	about.set_copyright("Copyright (c) 2004-2005 Nigel Tao.")
	about.set_license("This program is licenced under the GNU GPL.")
	about.set_authors(["Nigel Tao <nigel.tao@myrealbox.com>"])
	about.set_website("http://browserbookapp.sourceforge.net/deskbar.html")
	about.set_logo(deskbar.DESKBAR_BIG_IMAGE.get_pixbuf())
	about.show_all()
