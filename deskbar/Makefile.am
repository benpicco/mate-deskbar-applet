libexec_SCRIPTS = deskbar-applet

deskbardir = $(pythondir)/deskbar
deskbar_PYTHON = \
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
	
install-data-local:
	sed -e 's|\@DATADIR\@|$(datadir)|' __init__.py > $(deskbardir)/__init__.py

EXTRA_DIST = \
	__init__.py \
	$(libexec_SCRIPTS)
