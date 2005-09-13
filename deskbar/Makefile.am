SUBDIRS = iconentry

libexec_SCRIPTS = deskbar-applet

deskbardir = $(pythondir)/deskbar
deskbar_PYTHON = \
	__init__.py \
	defs.py \
	about.py \
	applet.py \
	browser_bookmarks_epiphany.py \
	browser_bookmarks_mozilla.py \
	config.py \
	handlers.py \
	handler_address_book.py \
	handler_browser_bookmarks.py \
	handler_file_system.py \
	handler_gtk_bookmarks.py \
	handler_prefix.py \
	handler_web_site.py \
	indexer.py \
	preferences.py
	
DISTCLEANFILES = \
	defs.py
	
EXTRA_DIST = \
	defs.py.in \
	$(libexec_SCRIPTS)
