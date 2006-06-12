SUBDIRS = specs

updaterbindir = $(libdir)/deskbar-applet
updaterbin_SCRIPTS = new-stuff-manager

updaterdir = $(pythondir)/deskbar/updater
updater_PYTHON = \
	__init__.py \
	NewStuffUpdater.py \
	ProgressbarDialog.py
	
# Dbus service file
servicedir = $(DBUS_SERVICES_DIR)
service_in_files = org.gnome.NewStuffManager.service.in
service_DATA = $(BUILT_FILES)

# Rule to make the service file with bindir expanded
$(service_DATA): $(service_in_files) Makefile
	@sed -e "s|\@libdir\@|$(libdir)|" $< > $@

BUILT_FILES = $(service_in_files:.service.in=.service)
CLEANFILES = $(BUILT_FILES)
EXTRA_DIST = new-stuff-manager $(service_in_files)
