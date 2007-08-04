INCLUDES = $(PYTHON_INCLUDES) $(DESKBAR_CFLAGS)

_gdmclientdir = $(pythondir)/deskbar/handlers/gdmclient
_gdmclient_LTLIBRARIES = _gdmclient.la
_gdmclient_la_LDFLAGS = -module -avoid-version -export-symbols-regex init_gdmclient
_gdmclient_la_LIBADD = $(DESKBAR_LIBS)
_gdmclient_la_SOURCES = 	\
	gdm-logout-action.h	\
	gdm-logout-action.c	\
        _gdmclientmodule.c

nodist__gdmclient_la_SOURCES = _gdmclient.c

_gdmclient_PYTHON =		\
	__init__.py

CLEANFILES = _gdmclient.c
EXTRA_DIST = 			\
	_gdmclient.defs		\
	_gdmclient.override

_gdmclient.c: _gdmclient.defs _gdmclient.override
.defs.c:
	(cd $(srcdir) \
	 && $(PYGTK_CODEGEN) \
	    --override $*.override \
	    --register $(PYGTK_DEFSDIR)/gtk-types.defs \
	    --register $(PYGTK_DEFSDIR)/gdk-types.defs \
	    --prefix py$* $*.defs) > gen-$*.c \
	 && cp gen-$*.c $*.c \
	 && rm -f gen-$*.c
