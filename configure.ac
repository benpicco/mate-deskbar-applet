AC_INIT(deskbar-applet, 0.8.4, raphael@slinckx.net)
AC_CONFIG_SRCDIR(deskbar/__init__.py)
AC_CONFIG_HEADERS(config.h)
AC_CONFIG_MACRO_DIR([m4])

AM_INIT_AUTOMAKE
GNOME_COMMON_INIT

AM_MAINTAINER_MODE
AM_DISABLE_STATIC
AM_PROG_LIBTOOL
AC_SUBST(ACLOCAL_AMFLAGS, "$ACLOCAL_FLAGS -I m4")
AC_PROG_CC

dnl ****************************************************************************
dnl * Pkg-Config
dnl ****************************************************************************
AC_CHECK_PROG(HAVE_PKGCONFIG, pkg-config, yes, no)
if test "x$HAVE_PKGCONFIG" = "xno"; then
  AC_MSG_ERROR(you need to have pkgconfig installed !)
fi

dnl ****************************************************************************
dnl * Translation & i18n
dnl ****************************************************************************
ALL_LINGUAS="en_GB fi ja nl zh_CN"
GETTEXT_PACKAGE="deskbar-applet"
AC_PROG_INTLTOOL([0.33])
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE", [The gettext package])
AM_GLIB_GNU_GETTEXT

dnl ****************************************************************************
dnl * GConf support
dnl ****************************************************************************
AC_PATH_PROG(GCONFTOOL, gconftool-2)
AM_GCONF_SOURCE_2

dnl ****************************************************************************
dnl * Python 2.3
dnl ****************************************************************************
AM_PATH_PYTHON(2.3)
AM_CHECK_PYTHON_HEADERS(,[AC_MSG_ERROR(could not find Python headers)])

AS_AC_EXPAND(DATADIR, $datadir)
AS_AC_EXPAND(LIBDIR, $libdir)
AC_SUBST(DATADIR)
AC_SUBST(LIBDIR)
AC_SUBST(VERSION)
AC_SUBST(PACKAGE)

dnl ****************************************************************************
dnl * PyGTK & co for Gnome Streamer
dnl ****************************************************************************
PKG_CHECK_MODULES(DESKBAR,
	gtk+-2.0				>= 2.6
	pygtk-2.0				>= 2.6
	pygobject-2.0			>= 2.6
	gnome-python-2.0			>= 2.10
	gnome-python-extras-2.0	>= 2.10
	gnome-python-extras-2.0	>= 2.10
)
AC_SUBST(DESKBAR_CFLAGS)
AC_SUBST(DESKBAR_LIBS)

dnl ****************************************************************************
dnl * Check for libbeagle to build the beagle handler
dnl ****************************************************************************
AC_ARG_ENABLE(beagle,
	AC_HELP_STRING([--disable-beagle], [Disable libbeagle support (default auto)]),
	enable_libbeagle=$enableval,
	enable_libbeagle=auto)

PKG_CHECK_MODULES(BEAGLE,
	libbeagle-0.0
	pygtk-2.0				>= 2.6
	pygobject-2.0			>= 2.6,
	have_libbeagle_dependencies=yes,
	have_libbeagle_dependencies=no)

if test "x$have_libbeagle_dependencies" = "xno"; then
	dnl error out if user has explicitly requested libbeagle
	if test "x$enable_libbeagle" = "xyes"; then
		AC_MSG_ERROR([Could not find libbeagle])
	fi
	enable_libbeagle="no (missing dependencies)"
else
	if test "x$enable_libbeagle" != "xno"; then
		enable_libbeagle="yes"
	else
		enable_libbeagle="no (disabled)"
	fi
fi
AM_CONDITIONAL(ENABLE_BEAGLE, test "x$enable_libbeagle" = "xyes")
AC_SUBST(BEAGLE_LIBS)
AC_SUBST(BEAGLE_CFLAGS)

dnl ****************************************************************************
dnl * Check for evolution's libebook to build the evolution handler
dnl ****************************************************************************
AC_ARG_ENABLE(evolution,
	AC_HELP_STRING([--disable-evolution], [Disable evolution's libebook support (default auto)]),
	enable_libebook=$enableval,
	enable_libebook=auto)

PKG_CHECK_MODULES(EVOLUTION,
	libebook-1.2
	gtk+-2.0				>= 2.6
	pygtk-2.0				>= 2.6
	pygobject-2.0			>= 2.6,
	have_libebook_dependencies=yes,
	have_libebook_dependencies=no)

if test "x$have_libebook_dependencies" = "xno"; then
	dnl error out if user has explicitly requested libebook
	if test "x$enable_libebook" = "xyes"; then
		AC_MSG_ERROR([Could not find evolution's libebook])
	fi
	enable_libebook="no (missing dependencies)"
else
	if test "x$enable_libebook" != "xno"; then
		enable_libebook="yes"
	else
		enable_libebook="no (disabled)"
	fi
fi
AM_CONDITIONAL(ENABLE_EVOLUTION, test "x$enable_libebook" = "xyes")
AC_SUBST(EVOLUTION_LIBS)
AC_SUBST(EVOLUTION_CFLAGS)

dnl ****************************************************************************
dnl * PyGTK Codegen and defs files
dnl ****************************************************************************
AC_PATH_PROG(PYGTK_CODEGEN, pygtk-codegen-2.0, no)
if test "x$PYGTK_CODEGEN" = xno; then
  AC_MSG_ERROR(could not find pygtk-codegen-2.0 script)
fi

AC_MSG_CHECKING(for pygtk defs)
PYGTK_DEFSDIR=`$PKG_CONFIG --variable=defsdir pygtk-2.0`
AC_SUBST(PYGTK_DEFSDIR)
AC_MSG_RESULT($PYGTK_DEFSDIR)

dnl ****************************************************************************
dnl * --------------------------------------------------------------------------
dnl ****************************************************************************
AC_OUTPUT([
Makefile
deskbar/Makefile
deskbar/defs.py
deskbar/evolution/Makefile
deskbar/handlers/Makefile
deskbar/iconentry/Makefile
deskbar/keybinder/Makefile
deskbar/beagle/Makefile
data/Makefile
data/deskbar-applet.pc
data/art/Makefile
po/Makefile.in
])

echo
echo $PACKAGE v$VERSION
echo

echo Prefix............... : $prefix
echo Evolution Support.... : $enable_libebook
echo Beagle Support ...... : $enable_libbeagle

echo
echo "Now type make to compile"
echo "Then su to root and type: make install"
echo
