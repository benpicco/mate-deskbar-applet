# ******************************************************************************
# Images and icon
# ******************************************************************************
artdir = $(pkgdatadir)/art
art_DATA = \
	deskbar-applet-panel-v.svg \
	deskbar-applet-panel-h.svg \
	deskbar-applet-panel-v.png \
	deskbar-applet-panel-h.png \
	deskbar-applet-small.png \
	delicious.png \
	folder-bookmark.png \
	generic.png \
	yahoo.png \
	google.png \
	epiphany-history.png
	
icondir = $(datadir)/icons/hicolor/48x48/apps
icon_DATA = deskbar-applet.png

svgicondir = $(datadir)/icons/hicolor/scalable/apps
svgicon_DATA = deskbar-applet.svg

gtk_update_icon_cache = gtk-update-icon-cache -f -t $(datadir)/icons/hicolor

install-data-hook:
	@-if test -z "$(DESTDIR)"; then \
		echo "Updating Gtk icon cache."; \
		$(gtk_update_icon_cache); \
	else \
		echo "*** Icon cache not updated.  After install, run this:"; \
		echo "***   $(gtk_update_icon_cache)"; \
	fi

EXTRA_DIST = \
	$(art_DATA)
	
