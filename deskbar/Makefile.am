SUBDIRS = iconentry handlers

libexec_SCRIPTS = deskbar-applet

deskbardir = $(pythondir)/deskbar
deskbar_PYTHON = \
	__init__.py \
	about.py \
	applet.py \
	defs.py \
	deskbarentry.py \
	indexer.py \
	ltihooks.py \
	preferences.py

DISTCLEANFILES = \
	defs.py
	
EXTRA_DIST = \
	defs.py.in \
	$(libexec_SCRIPTS)
