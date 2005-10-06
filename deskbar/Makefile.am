SUBDIRS = iconentry keybinder handlers

libexec_SCRIPTS = deskbar-applet

deskbardir = $(pythondir)/deskbar
deskbar_PYTHON = \
	__init__.py \
	about.py \
	applet.py \
	applet_keybinder.py \
	defs.py \
	deskbarentry.py \
	handler.py \
	handler_utils.py \
	indexer.py \
	ltihooks.py \
	tokenizer.py \
	module_list.py \
	preferences.py

DISTCLEANFILES = \
	defs.py
	
EXTRA_DIST = \
	defs.py.in \
	$(libexec_SCRIPTS)
