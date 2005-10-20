INCLUDES = $(PYTHON_INCLUDES) $(BEAGLE_CFLAGS)

_beagledir = $(pythondir)/deskbar/beagle
_beagle_LTLIBRARIES = _beagle.la
_beagle_la_LDFLAGS = -module -avoid-version -export-symbols-regex init_beagle
_beagle_la_LIBADD = $(BEAGLE_LIBS)
_beagle_la_SOURCES = \
	_beaglemodule.c 

nodist__beagle_la_SOURCES = _beagle.c

_beagle_PYTHON = \
	__init__.py

CLEANFILES = _beagle.c
EXTRA_DIST = \
	_beagle.defs \
	_beagle.override \
	gen-defs.sh

_beagle.c: _beagle.defs _beagle.override
.defs.c:
	(cd $(srcdir) \
	 && $(PYGTK_CODEGEN) \
	    --override $*.override \
	    --register $(PYGTK_DEFSDIR)/gtk-types.defs \
	    --register $(PYGTK_DEFSDIR)/gdk-types.defs \
	    --prefix py$* $*.defs) > gen-$*.c \
	&& cp gen-$*.c $*.c \
	&& rm -f gen-$*.c

