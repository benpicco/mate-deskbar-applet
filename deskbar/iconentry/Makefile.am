INCLUDES = $(PYTHON_INCLUDES) $(DESKBAR_CFLAGS)

_iconentrydir = $(pythondir)/deskbar/iconentry
_iconentry_LTLIBRARIES = _iconentry.la
_iconentry_la_LDFLAGS = -module -avoid-version -export-symbols-regex init_iconentry
_iconentry_la_LIBADD = $(DESKBAR_LIBS)
_iconentry_la_SOURCES = \
	_iconentrymodule.c \
	ephy-icon-entry.c \
	ephy-icon-entry.h

nodist__iconentry_la_SOURCES = _iconentry.c

_iconentry_PYTHON = \
	__init__.py

CLEANFILES = _iconentry.c
EXTRA_DIST = \
	_iconentry.defs \
	_iconentry.override \
	gen-defs.sh

_iconentry.c: _iconentry.defs _iconentry.override
.defs.c:
	(cd $(srcdir) \
	 && $(PYGTK_CODEGEN) \
	    --override $*.override \
	    --register $(PYGTK_DEFSDIR)/gtk-types.defs \
	    --register $(PYGTK_DEFSDIR)/gdk-types.defs \
	    --prefix py$* $*.defs) > gen-$*.c \
	&& cp gen-$*.c $*.c \
	&& rm -f gen-$*.c

