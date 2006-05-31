SUBDIRS = ui handlers iconentry keybinder gnomedesktop gdmclient osutils

if ENABLE_EVOLUTION
SUBDIRS += evolution
endif
	
deskbar-applet: deskbar-applet.py
	sed -e "s|\@PYTHONDIR\@|$(pythondir)/deskbar|" $< > $@

deskbarbindir = $(libdir)/deskbar-applet
deskbarbin_SCRIPTS = deskbar-applet

deskbardir = $(pythondir)/deskbar
deskbar_PYTHON = \
	defs.py \
	gtkexcepthook.py \
	BrowserMatch.py \
	Categories.py \
	DeskbarApplet.py \
	DeskbarAppletPreferences.py \
	DeskbarHistory.py \
	Handler.py \
	Indexer.py \
	__init__.py \
	Keybinder.py \
	Match.py \
	ModuleContext.py \
	ModuleList.py \
	ModuleLoader.py \
	Utils.py \
	Watcher.py
	
BUILT_SOURCES = \
	deskbar-applet
	
CLEANFILES = \
	$(BUILT_SOURCES)
	
DISTCLEANFILES = \
	defs.py \
	$(CLEANFILES)
	
EXTRA_DIST = \
	defs.py.in \
	deskbar-applet.py
