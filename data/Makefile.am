SUBDIRS = art

# ******************************************************************************
# Panel applet matecomponent stuff
# ******************************************************************************
pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_in_files = deskbar-applet.pc.in
pkgconfig_DATA = $(pkgconfig_in_files:.pc.in=.pc)

# ******************************************************************************
# Panel applet matecomponent stuff
# ******************************************************************************
serverdir = $(libdir)/matecomponent/servers
server_in_files = Deskbar_Applet.server.in
server_DATA = $(server_in_files:.server.in=.server)

# ******************************************************************************
# MateConf Schemas
# ******************************************************************************
# MateConf Preference Schemas
schemadir = $(MATECONF_SCHEMA_FILE_DIR)
schema_in_files = deskbar-applet.schemas.in
schema_DATA = $(schema_in_files:.schemas.in=.schemas)

# ******************************************************************************
# Misc data
# ******************************************************************************
resourcesdir = $(pkgdatadir)
resources_DATA = \
	Deskbar_Applet.xml \
	mozilla-search.ui \
	smart-bookmarks.ui \
	prefs-dialog.ui

deskbarbindir = $(libexecdir)/deskbar-applet

#
# Desktop file
#
#desktopdir = $(datadir)/applications
#desktop_in_files = deskbar-applet.desktop.in 
#desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)

# ******************************************************************************
# Build rules
# ******************************************************************************
@INTLTOOL_DESKTOP_RULE@
@INTLTOOL_SERVER_RULE@
@INTLTOOL_SCHEMAS_RULE@

$(server_in_files): $(server_in_files:.server.in=.server.in.in)
	$(AM_V_GEN)sed -e "s|\@LIBEXECDIR\@|$(deskbarbindir)|" $< > $@

if MATECONF_SCHEMAS_INSTALL
install-data-local: install-schemas
install-schemas:
	MATECONF_CONFIG_SOURCE=$(MATECONF_SCHEMA_CONFIG_SOURCE) \
		$(MATECONFTOOL) --makefile-install-rule $(schema_DATA)
endif

DISTCLEANFILES = \
	$(schema_DATA) \
	$(server_DATA) \
	$(server_in_files) \
	$(pkgconfig_DATA)
#	$(desktop_DATA)

EXTRA_DIST = \
	$(schema_in_files) \
	Deskbar_Applet.server.in.in \
	$(resources_DATA) \
	$(pkgconfig_in_files)
#	deskbar-applet.desktop.in.in 
	
	
