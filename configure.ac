AC_INIT(deskbar-applet, 0.4.0, mail@mail.com)
AC_CONFIG_SRCDIR(deskbar/__init__.py.in)
AC_CONFIG_HEADERS(config.h)

AM_INIT_AUTOMAKE

AM_MAINTAINER_MODE
AM_DISABLE_STATIC
AM_PROG_LIBTOOL
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
ALL_LINGUAS="en_GB"
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
AS_AC_EXPAND(DATADIR, $datadir)
AC_SUBST(DATADIR)

dnl ****************************************************************************
dnl * PyGTK & co for Gnome Streamer
dnl ****************************************************************************
PKG_CHECK_MODULES(DESKBAR,
	pygtk-2.0				>= 2.6
	pygobject-2.0			>= 2.6
	gnome-python-2.0			>= 2.10
	gnome-python-extras-2.0	>= 2.10
	libsexy					>= 0.1
)

dnl ****************************************************************************
dnl * --------------------------------------------------------------------------
dnl ****************************************************************************
AC_OUTPUT([
Makefile
deskbar/Makefile
deskbar/__init__.py
data/Makefile
data/art/Makefile
po/Makefile.in
])

echo
echo $PACKAGE v$VERSION
echo

echo Prefix............... : $prefix

echo
echo "Now type make to compile"
echo "Then su to root and type: make install"
echo
