SUBDIRS = art

# ******************************************************************************
# Panel applet bonobo stuff
# ******************************************************************************
serverdir = $(libdir)/bonobo/servers
server_in_files = Deskbar_Applet.server.in
server_DATA = $(server_in_files:.server.in=.server)

# ******************************************************************************
# Preferences window UIManager
# ******************************************************************************
uidir   = $(datadir)/gnome-2.0/ui
ui_DATA = Deskbar_Applet.xml

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
	default-engine-prefix.txt \
	default-engines.txt \
	prefs-dialog.glade


# ******************************************************************************
# Build rules
# ******************************************************************************
@INTLTOOL_SERVER_RULE@
@INTLTOOL_SCHEMAS_RULE@

$(server_in_files): $(server_in_files:.server.in=.server.in.in)
	sed -e "s|\@LIBEXECDIR\@|$(libexecdir)|" $< > $@

install-data-local:
        GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) \
                gconftool-2 --makefile-install-rule $(schema_DATA)

DISTCLEANFILES = \
	$(schema_DATA) \
	$(server_DATA) \
	$(server_in_files) 

EXTRA_DIST = \
	$(schema_in_files) \
	Deskbar_Applet.server.in.in \
	$(ui_DATA) \
	$(resources_DATA)
	
	
