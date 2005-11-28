SUBDIRS = art

# ******************************************************************************
# Panel applet bonobo stuff
# ******************************************************************************
pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_in_files = deskbar-applet.pc.in
pkgconfig_DATA = $(pkgconfig_in_files:.pc.in=.pc)

# ******************************************************************************
# Panel applet bonobo stuff
# ******************************************************************************
serverdir = $(libdir)/bonobo/servers
server_in_files = Deskbar_Applet.server.in
server_DATA = $(server_in_files:.server.in=.server)

# ******************************************************************************
# GConf Schemas
# ******************************************************************************
# GConf Preference Schemas
schemadir = $(GCONF_SCHEMA_FILE_DIR)
schema_in_files = deskbar-applet.schemas.in
schema_DATA = $(schema_in_files:.schemas.in=.schemas)

# ******************************************************************************
# Misc data
# ******************************************************************************
resourcesdir = $(pkgdatadir)
resources_DATA = \
	Deskbar_Applet.xml \
	smart-bookmarks.glade \
	prefs-dialog.glade

deskbarbindir = $(libdir)/deskbar-applet

# ******************************************************************************
# Build rules
# ******************************************************************************
@INTLTOOL_SERVER_RULE@
@INTLTOOL_SCHEMAS_RULE@

$(server_in_files): $(server_in_files:.server.in=.server.in.in)
	sed -e "s|\@LIBEXECDIR\@|$(deskbarbindir)|" $< > $@

if GCONF_SCHEMAS_INSTALL
install-data-local: install-schemas
install-schemas:
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) \
		$(GCONFTOOL) --makefile-install-rule $(schema_DATA)
endif

DISTCLEANFILES = \
	$(schema_DATA) \
	$(server_DATA) \
	$(server_in_files) \
	$(pkgconfig_DATA)

EXTRA_DIST = \
	$(schema_in_files) \
	Deskbar_Applet.server.in.in \
	$(resources_DATA) \
	$(pkgconfig_in_files)
	
	
