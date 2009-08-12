INCLUDES = $(PYTHON_INCLUDES) $(DESKBAR_CFLAGS)

_osutilsdir = $(pythondir)/deskbar/osutils
_osutils_LTLIBRARIES = _osutils.la
_osutils_la_LDFLAGS = -module -avoid-version -export-symbols-regex init_osutils
_osutils_la_LIBADD = $(DESKBAR_LIBS)
_osutils_la_SOURCES = \
	_osutilsmodule.c

_osutils_PYTHON = \
	__init__.py
