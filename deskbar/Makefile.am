SUBDIRS = handlers iconentry keybinder

if ENABLE_BEAGLE
SUBDIRS += beagle
endif

if ENABLE_EVOLUTION
SUBDIRS += evolution
endif
	
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
	handlers_browsers.py \
	indexer.py \
	locale_utils.py \
	ltihooks.py \
	tokenizer.py \
	module_list.py \
	preferences.py

DISTCLEANFILES = \
	defs.py
	
EXTRA_DIST = \
	defs.py.in \
	$(libexec_SCRIPTS)
