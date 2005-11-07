INCLUDES = $(PYTHON_INCLUDES) $(DESKBAR_CFLAGS)

_gnomedesktopdir = $(pythondir)/deskbar/gnomedesktop
_gnomedesktop_LTLIBRARIES = _gnomedesktop.la
_gnomedesktop_la_LDFLAGS = -module -avoid-version -export-symbols-regex init_gnomedesktop
_gnomedesktop_la_LIBADD = $(DESKBAR_LIBS)
_gnomedesktop_la_SOURCES = \
	_gnomedesktopmodule.c 

nodist__gnomedesktop_la_SOURCES = _gnomedesktop.c

_gnomedesktop_PYTHON = \
	__init__.py

CLEANFILES = _gnomedesktop.c
EXTRA_DIST = \
	_gnomedesktop.defs \
	_gnomedesktop.override

_gnomedesktop.c: _gnomedesktop.defs _gnomedesktop.override
.defs.c:
	(cd $(srcdir) \
	 && $(PYGTK_CODEGEN) \
	    --override $*.override \
	    --register $(PYGTK_DEFSDIR)/gtk-types.defs \
	    --register $(PYGTK_DEFSDIR)/gdk-types.defs \
	    --prefix py$* $*.defs) > gen-$*.c \
	&& cp gen-$*.c $*.c \
	&& rm -f gen-$*.c
