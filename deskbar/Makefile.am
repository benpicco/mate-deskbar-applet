SUBDIRS = core handlers interfaces osutils ui

deskbar-applet: deskbar-applet.py
	cp -f $< $@
	
deskbarbindir = $(libexecdir)/deskbar-applet
deskbarbin_SCRIPTS = deskbar-applet

deskbardir = $(pythondir)/deskbar
deskbar_PYTHON = \
	defs.py \
	gtkexcepthook.py \
	__init__.py
	
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
