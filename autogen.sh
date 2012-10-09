#!/bin/sh
# Run this to generate all the initial makefiles, etc.

srcdir=`dirname $0`
test -z "$srcdir" && srcdir=.
touch ChangeLog

PKG_NAME="deskbar-applet"
ACLOCAL_FLAGS="$ACLOCAL_FLAGS -I m4"
REQUIRED_AUTOCONF_VERSION=2.60
REQUIRED_AUTOMAKE_VERSION=1.9.2
REQUIRED_MACROS="python.m4"

(test -f $srcdir/configure.ac \
  && test -f $srcdir/autogen.sh) || {
    echo -n "**Error**: Directory "\`$srcdir\'" does not look like the"
    echo " top-level $PKG_NAME directory"
    exit 1
}

DIE=0

mate_autogen=
mate_datadir=

ifs_save="$IFS"; IFS=":"
for dir in $PATH ; do
  test -z "$dir" && dir=.
  if test -f $dir/mate-autogen ; then
    mate_autogen="$dir/mate-autogen"
    mate_datadir=`echo $dir | sed -e 's,/bin$,/share,'`
    break
  fi
done
IFS="$ifs_save"

if test -z "$mate_autogen" ; then
  echo "You need to install the mate-common module and make"
  echo "sure the mate-autogen script is in your \$PATH."
  exit 1
fi

MATE_DATADIR="$mate_datadir" USE_MATE2_MACROS=1 . $mate_autogen
