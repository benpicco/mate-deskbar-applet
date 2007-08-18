SUBDIRS = actions gdmclient

if ENABLE_EVOLUTION
SUBDIRS += evolution
endif

deskbar_handlers_modulesdir = $(pythondir)/deskbar/handlers
deskbar_handlers_modules_PYTHON = __init__.py

deskbar_handlersdir = $(libdir)/deskbar-applet/modules
deskbar_handlers_PYTHON = \
	beagle-static.py \
	beagle-live.py \
	desklicious.py \
	epiphany.py \
	files.py \
	gdmactions.py \
	history.py \
	iswitch-window.py \
	mozilla.py \
	programs.py \
	recent.py \
	web_address.py \
	yahoo.py

if ENABLE_EVOLUTION
deskbar_handlers_PYTHON += evolution.py
endif

EXTRA_DIST = 

