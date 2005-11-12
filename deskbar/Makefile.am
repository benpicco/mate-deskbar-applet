SUBDIRS = handlers iconentry keybinder gnomedesktop

if ENABLE_BEAGLE
SUBDIRS += beagle
endif

if ENABLE_EVOLUTION
SUBDIRS += evolution
endif
	
deskbar-applet: deskbar-applet.py
	sed -e "s|\@PYTHONPATH\@|$(pythondir)/deskbar|" $< > $@

defs.py: defs.py.in
	sed -e "s|\@DATADIR\@|$(datadir)|" \
		-e "s|\@LIBDIR\@|$(libdir)|" \
		-e "s|\@VERSION\@|$(VERSION)|" \
		-e "s|\@PACKAGE\@|$(PACKAGE)|" \
		-e "s|\@PYTHONPATH\@|$(pythondir)/deskbar|" \
		$< > $@

deskbarbindir = $(libdir)/deskbar-applet
deskbarbin_SCRIPTS = deskbar-applet

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

BUILT_SOURCES = \
	defs.py \
	deskbar-applet
	
CLEANFILES = \
	$(BUILT_SOURCES)
	
DISTCLEANFILES = \
	$(CLEANFILES)
	
EXTRA_DIST = \
	defs.py.in \
	deskbar-applet.py
