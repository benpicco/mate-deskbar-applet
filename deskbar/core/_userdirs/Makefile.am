INCLUDES = $(PYTHON_INCLUDES) $(DESKBAR_CFLAGS) $(GLIB_CFLAGS)

__userdirsdir = $(pyexecdir)/deskbar/core/_userdirs
__userdirs_LTLIBRARIES = __userdirs.la
__userdirs_la_LDFLAGS = -module -avoid-version -export-symbols-regex init__userdirs
__userdirs_la_LIBADD = $(DESKBAR_LIBS) $(GLIB_LIBS)
__userdirs_la_SOURCES = \
	__userdirsmodule.c 

__userdirs_PYTHON = \
	__init__.py
