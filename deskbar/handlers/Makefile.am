SUBDIRS = actions gdmclient

if ENABLE_EVOLUTION
SUBDIRS += evolution
endif

deskbar_handlers_modulesdir = $(pythondir)/deskbar/handlers
deskbar_handlers_modules_PYTHON = __init__.py

deskbar_handlersdir = $(libdir)/deskbar-applet/modules-2.20-compatible
deskbar_handlers_PYTHON = \
	beagle-static.py \
	beagle-live.py \
	calculator.py \
	desklicious.py \
	epiphany.py \
	files.py \
	gdmactions.py \
	googlecodesearch.py \
	googlesearch.py \
	history.py \
	iswitch-window.py \
	mozilla.py \
	programs.py \
	recent.py \
	templates.py \
	tomboy.py \
	twitter.py \
	web_address.py \
	wikipedia-suggest.py \
	yahoo.py

if ENABLE_EVOLUTION
deskbar_handlers_PYTHON += evolution.py
endif

EXTRA_DIST = 

