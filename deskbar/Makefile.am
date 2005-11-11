SUBDIRS = handlers iconentry keybinder gnomedesktop

if ENABLE_BEAGLE
SUBDIRS += beagle
endif

if ENABLE_EVOLUTION
SUBDIRS += evolution
endif
	
deskbarbindir = $(libdir)/deskbar-applet
deskbarbin_SCRIPTS = deskbar-applet

deskbar-applet: deskbar-applet.py
	sed -e "s|\@PYTHONPATH\@|$(pythondir)/deskbar|" $< > $@
        
deskbardir = $(pythondir)/deskbar
deskbar_PYTHON = \
	__init__.py \
	about.py \
	applet.py \
	applet_keybinder.py \
	defs.py \
	deskbarentry.py \
	filewatcher.py \
	handler.py \
	handler_utils.py \
	handlers_browsers.py \
	indexer.py \
	locale_utils.py \
	ltihooks.py \
	tokenizer.py \
	module_list.py \
	preferences.py

CLEANFILES = \
	deskbar-applet
	
DISTCLEANFILES = \
	deskbar-applet \
	defs.py
	
EXTRA_DIST = \
	defs.py.in \
	deskbar-applet.py
